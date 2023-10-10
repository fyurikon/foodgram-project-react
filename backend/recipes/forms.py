from django import forms
from django.core.exceptions import ValidationError

from .models import Recipe


class RecipeForm(forms.ModelForm):
    """Form for recipe."""
    class Meta:
        model = Recipe
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        ingredients = cleaned_data.get('ingredients')

        if not ingredients:
            raise ValidationError(
                'Необходимо добавить хотя бы один ингредиент.'
            )
