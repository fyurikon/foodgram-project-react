from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

MAX_LENGTH = 254
MEAS_MAX_LENGTH = 24
COLOR_MAX_LENGTH = 7


class Tag(models.Model):
    """Tag model."""
    name = models.CharField(
        'Тэг',
        max_length=MAX_LENGTH,
        unique=True
    )
    color = models.CharField(
        'Цвет',
        max_length=COLOR_MAX_LENGTH,
        unique=True
    )
    slug = models.SlugField(
        'Слаг',
        unique=True,
        max_length=MAX_LENGTH
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        """String representation."""
        return self.name


class Ingredient(models.Model):
    """Ingredient model."""
    name = models.CharField(
        'Ингредиент',
        max_length=MAX_LENGTH
    )
    measurement_unit = models.CharField(
        'ед. изм.',
        max_length=MEAS_MAX_LENGTH
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        """String representation."""
        return self.name


class Recipe(models.Model):
    """Recipe model."""
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Автор'
    )
    name = models.CharField('Рецепт', max_length=MAX_LENGTH)
    image = models.ImageField(
        'Картинка',
        upload_to='recipes/images/'
    )
    description = models.TextField('Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        related_name='recipes',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Тэги'
    )
    cooking_time = models.PositiveIntegerField(
        'Время готовки'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        """String representation."""
        return self.name


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_list',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    quantity = models.PositiveIntegerField(
        'Количество'
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'

    def __str__(self):
        """String representation."""
        return f"{self.ingredient.name} in {self.recipe.name}"


class Favorite(models.Model):
    """Favorite model."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Избранный'
        verbose_name_plural = 'Избранные'

    def __str__(self):
        """String representation."""
        return f'{self.user} add to favorite {self.recipe}'


class ShoppingCart(models.Model):
    """Shopping cart model."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'

    def __str__(self):
        return f'{self.user} add to cart {self.recipe}'
