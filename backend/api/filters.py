from django.contrib.auth import get_user_model
from django.db.models import Q
from django_filters import FilterSet, filters
from rest_framework.filters import SearchFilter

from recipes.models import Tag, Recipe, Favorite

User = get_user_model()


class IngredientFilter(SearchFilter):
    """Filter by name."""
    search_param = 'name'


class RecipeFilter(FilterSet):
    """
    Recipe filter allows you to filter by:
    -) Author
    -) Tag
    -) Is recipe in the shopping cart
    -) Is recipe in favorite.
    """
    author = filters.AllValuesMultipleFilter(
        field_name='author__id'
    )

    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )

    is_in_shopping_cart = filters.NumberFilter(
        method='get_is_in_shopping_cart',
        label='shopping_cart',
    )

    is_favorited = filters.NumberFilter(
        method='get_is_favorited',
        label='favorite',
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def get_is_favorited(self, queryset, name, value):
        """Filter checks if the recipe is in favorite."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(
                favorite__user=self.request.user
            )
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        """Filter checks if the recipe is in the cart."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(
                shoppingcart__user=self.request.user
            )
        return queryset
