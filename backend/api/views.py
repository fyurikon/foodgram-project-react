from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from api.filters import IngredientFilter
from api.pagination import CustomPagination
from api.serializers import TagSerializer, IngredientSerializer, FollowSerializer, CustomUserSerializer
from recipes.models import Tag, Ingredient
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
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination
    link_model = Follow

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
            subscription = get_object_or_404(
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
        serializer = FollowSerializer(pages, many=True)

        return self.get_paginated_response(serializer.data)
