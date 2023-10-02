from django.contrib.auth import get_user_model
from rest_framework.filters import SearchFilter


User = get_user_model()


class IngredientFilter(SearchFilter):
    """Filter by name."""
    search_param = 'name'
