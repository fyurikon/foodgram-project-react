from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef, Sum
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.filters import IngredientFilter
from api.pagination import CustomPagination
from api.permissions import IsAdminOrAuthorOrReadOnly
from api.serializers import (CustomUserSerializer, FollowSerializer,
                             IngredientSerializer, RecipeCompactSerializer,
                             RecipeCreateSerializer, RecipeGetSerializer,
                             TagSerializer)

from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Follow

User = get_user_model()


class TagViewSet(ReadOnlyModelViewSet):
    """Tag viewset."""
    permission_classes = (AllowAny,)
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    """Ingredient viewset."""
    permission_classes = (AllowAny,)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (IngredientFilter, )
    search_fields = ('^name', )


class CustomUserViewSet(UserViewSet):
    """Custom user viewset."""
    permission_classes = (IsAdminOrAuthorOrReadOnly,)
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination
    link_model = Follow

    def retrieve(self, request, *args, **kwargs):
        if request.user.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return super().retrieve(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def current_user(self, request):
        if request.user.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=('post', 'delete', ),
        permission_classes=(IsAuthenticated, )
    )
    def subscribe(self, request, **kwargs):
        """Subscribe to the user."""
        user = request.user
        following_id = self.kwargs.get('id')
        following = get_object_or_404(User, id=following_id)

        if request.method == 'POST':
            serializer = FollowSerializer(
                following,
                data=request.data,
                context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            Follow.objects.create(user=user, following=following)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            subscription = get_object_or_400(
                Follow,
                user=user,
                following=following
            )
            subscription.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('get', ),
        permission_classes=(IsAuthenticated, )
    )
    def subscriptions(self, request):
        """Return all subscriptions of the user."""
        pages = self.paginate_queryset(
            User.objects.filter(following__user=self.request.user)
        )
        serializer = FollowSerializer(
            pages,
            many=True,
            context={'request': request}
        )

        return self.get_paginated_response(serializer.data)


def get_object_or_400(klass, *args, **kwargs):
    try:
        return get_object_or_404(klass, *args, **kwargs)
    except Http404:
        raise ValidationError(
            {'not_exist': 'Объекта не существует!'}
        )


class RecipeViewSet(ModelViewSet):
    """Recipe viewset."""
    queryset = Recipe.objects.select_related('author')
    # queryset = Recipe.objects.perfetch_related('author')
    permission_classes = (
        IsAdminOrAuthorOrReadOnly,
    )
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication credentials were not provided.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def get_serializer_class(self):
        """Get serializer class."""
        if self.request.method in SAFE_METHODS:
            return RecipeGetSerializer
        return RecipeCreateSerializer

    def list(self, request, *args, **kwargs):
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart'
        )
        is_favorited = self.request.query_params.get('is_favorited')

        if is_in_shopping_cart or is_favorited:
            if not request.user.is_authenticated:
                return Response(
                    {'error': 'Authentication credentials were not provided.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        """Get recipes with filtering."""
        queryset = super().get_queryset()
        author = self.request.query_params.get('author')
        tags = self.request.query_params.getlist('tags')
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart'
        )
        is_favorited = self.request.query_params.get('is_favorited')

        if author:
            queryset = queryset.filter(author=author)

        if tags:
            queryset = queryset.filter(tags__slug__in=tags)

        if is_in_shopping_cart or is_favorited:
            if not self.request.user.is_authenticated:
                return queryset.none()

        if is_in_shopping_cart:
            queryset = queryset.annotate(
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=self.request.user,
                        recipe=OuterRef('pk')
                    )
                )
            )
            if is_in_shopping_cart == '1':
                queryset = queryset.filter(is_in_shopping_cart=True)
            else:
                queryset = queryset.filter(is_in_shopping_cart=False)

        if is_favorited:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user=self.request.user,
                        recipe=OuterRef('pk')
                    )
                )
            )
            if is_favorited == '1':
                queryset = queryset.filter(is_favorited=True)
            else:
                queryset = queryset.filter(is_favorited=False)

        return queryset.distinct()

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        """Add to favorite and delete from favorite."""
        recipe = get_object_or_400(Recipe, id=pk)

        if request.method == 'POST':
            if Favorite.objects.filter(
                    user=request.user,
                    recipe=recipe
            ).exists():
                return Response(
                    {'errors': 'Рецепт уже в избранном!'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            Favorite.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeCompactSerializer(recipe)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        else:
            obj = Favorite.objects.filter(user=request.user, recipe=recipe)
            if obj.exists():
                obj.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'errors': 'Рецепт уже удален!'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        """Add to cart and delete from cart."""
        recipe = get_object_or_400(Recipe, id=pk)

        if request.method == 'POST':
            if ShoppingCart.objects.filter(
                    user=request.user,
                    recipe=recipe
            ).exists():
                return Response(
                    {'errors': 'Рецепт уже в корзине!'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeCompactSerializer(recipe)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        else:
            obj = ShoppingCart.objects.filter(user=request.user, recipe=recipe)
            if obj.exists():
                obj.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'errors': 'Рецепт уже удален!'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        """Download shopping cart."""
        user = request.user
        if not user.shopping_cart.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        ingredients = IngredientInRecipe.objects.filter(
            recipe__shopping_cart__user=user
        ).values_list(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))

        shopping_list = [
            f'- {ingredient[0]} ({ingredient[1]}) - {ingredient[2]}'
            for ingredient in ingredients
        ]
        shopping_list = '\n'.join(shopping_list)

        filename = f'{user.username}_shopping_list.txt'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response
