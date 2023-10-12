from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.core.exceptions import ValidationError

from .models import Recipe, IngredientInRecipe, Ingredient


class IngredientForm(forms.ModelForm):
    """Form for selecting an ingredient."""
    class Meta:
        model = Ingredient
        fields = ('name',)


class IngredientInRecipeForm(forms.ModelForm):
    """Form for entering ingredient amount."""
    class Meta:
        model = IngredientInRecipe
        fields = ('ingredient', 'amount')


class RecipeForm(forms.ModelForm):
    """Form for recipe."""
    class Meta:
        model = Recipe
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        ingredients = cleaned_data.get('ingredients')

        if ingredients:
            ingredient_ids = [ingredient.id for ingredient in ingredients]
            if len(set(ingredient_ids)) != len(ingredient_ids):
                raise forms.ValidationError(
                    'Рецепт содержит повторяющиеся ингредиенты.'
                )

        return cleaned_data


class CustomIngredientInRecipeFormSet(BaseInlineFormSet):
    """Custom formset for ingredient in recipe."""
    def clean(self):
        super().clean()
        ingredients_count = sum(
            1 for form in self.forms if form.cleaned_data.get('ingredient')
        )
        if ingredients_count < 1:
            raise ValidationError("Требуется минимум 1 ингредиент в рецепте.")


IngredientInRecipeFormSet = inlineformset_factory(
    Recipe,
    IngredientInRecipe,
    form=IngredientInRecipeForm,
    formset=CustomIngredientInRecipeFormSet,
    extra=1,
    can_delete=True,
)
