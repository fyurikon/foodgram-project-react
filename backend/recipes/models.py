from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

User = get_user_model()

MAX_LENGTH = 200
MEAS_MAX_LENGTH = 24
COLOR_MAX_LENGTH = 7
STR_TEXT_LIMIT = 15
MIN_TIME = 1
MIN_PSIF = 0
MAX_PSIF = 32767


class Tag(models.Model):
    """Tag model."""
    name = models.CharField(
        'Тэг',
        max_length=MAX_LENGTH,
        unique=True
    )
    color = ColorField(
        'Цвет',
        max_length=COLOR_MAX_LENGTH,
        unique=True
    )
    slug = models.SlugField(
        'Слаг',
        max_length=MAX_LENGTH,
        unique=True
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        """String representation."""
        return self.name[:STR_TEXT_LIMIT]


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
        unique_together = ('name', 'measurement_unit')

    def __str__(self):
        """String representation."""
        return self.name[:STR_TEXT_LIMIT]


class Recipe(models.Model):
    """Recipe model."""
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    name = models.CharField('Рецепт', max_length=MAX_LENGTH)
    image = models.ImageField(
        'Картинка',
        upload_to='recipes/images/'
    )
    text = models.TextField('Описание')
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
    cooking_time = models.PositiveSmallIntegerField(
        'Время готовки',
        validators=(
            MinValueValidator(
                MIN_TIME, message=f'Минимальное время = {MIN_TIME}'
            ),
            MaxValueValidator(
                MAX_PSIF, message=f'Максимальное время =  {MAX_PSIF}'
            )
        )
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        """String representation."""
        return self.name[:STR_TEXT_LIMIT]


class IngredientInRecipe(models.Model):
    """Ingredient in recipe model."""
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
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=(
            MinValueValidator(
                MIN_PSIF, message=f'Мин кол-во д. б. > {MIN_PSIF}'
            ),
            MaxValueValidator(
                MAX_PSIF, message=f'Макс кол-во д. б. <=  {MAX_PSIF}'
            )
        )
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'

    def __str__(self):
        """String representation."""
        return (f"{self.ingredient.name[:STR_TEXT_LIMIT]} "
                f"{self.amount} in "
                f"{self.recipe.name[:STR_TEXT_LIMIT]}")


class BaseItem(models.Model):
    """Base abstract model for favorite and shopping cart items."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True
        unique_together = ('user', 'recipe')


class Favorite(BaseItem):
    """Favorite model."""

    class Meta:
        verbose_name = 'Избранный'
        verbose_name_plural = 'Избранные'

    def __str__(self):
        """String representation."""
        return (f'{self.user.username[:STR_TEXT_LIMIT]} add to '
                f'favorite {self.recipe.title[:STR_TEXT_LIMIT]}')


class ShoppingCart(BaseItem):
    """Shopping cart model."""

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'

    def __str__(self):
        """String representation."""
        return (f'{self.user.username[:STR_TEXT_LIMIT]} add to '
                f'cart {self.recipe.title[:STR_TEXT_LIMIT]}')
