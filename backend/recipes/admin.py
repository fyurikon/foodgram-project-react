from django.contrib import admin

from .models import (Favorite, Ingredient, IngredientInRecipe,
                     Recipe, ShoppingCart, Tag)
from .forms import (RecipeForm, IngredientForm,
                    IngredientInRecipeFormSet)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug',)
    search_fields = ('name', 'slug',)
    empty_value_display = '-пусто-'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    form = IngredientForm
    list_display = ('name', 'measurement_unit',)
    search_fields = ('name',)
    list_filter = ('name',)


class IngredientInRecipeInline(admin.TabularInline):
    """Inline form for IngredientInRecipe."""
    model = IngredientInRecipe
    formset = IngredientInRecipeFormSet
    extra = 1
    can_delete = False


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    form = RecipeForm
    inlines = [IngredientInRecipeInline]

    list_display = (
        'id',
        'name',
        'author',
        'text',
        'count_favorites',
    )
    readonly_fields = ('count_favorites',)
    search_fields = ('author', 'name',)
    list_filter = ('author', 'name',)

    @admin.display(description='Число добавлений в избранное')
    def count_favorites(self, obj):
        return obj.favorite_set.count()


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)
    search_fields = ('user', 'recipe',)
    list_filter = ('user', 'recipe',)
    empty_value_display = '-пусто-'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)
    search_fields = ('user', 'recipe',)
    list_filter = ('user', 'recipe',)
    empty_value_display = '-пусто-'


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount',)
    search_fields = ('recipe', 'ingredient',)
    list_filter = ('recipe', 'ingredient',)
    empty_value_display = '-пусто-'
