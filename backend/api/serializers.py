import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db.models import F
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField, IntegerField
from rest_framework.serializers import (
    ModelSerializer,
    ImageField,
    PrimaryKeyRelatedField
)

from recipes.models import Tag, Ingredient, Recipe, IngredientInRecipe
from users.models import Follow

User = get_user_model()


class CustomUserSerializer(ModelSerializer):
    """Custom user serializer."""
    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = get_user_model()
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Follow.objects.filter(user=user, following=obj).exists()
        return False


class CustomUserCreateSerializer(UserCreateSerializer):
    """Create custom user serializer."""
    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )


class TagSerializer(ModelSerializer):
    """Tag serializer."""
    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'color',
            'slug'
        )


class IngredientSerializer(ModelSerializer):
    """Ingredient serializer."""
    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit'
        )


class Base64ImageField(ImageField):
    """Image field for the image."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class RecipeCompactSerializer(ModelSerializer):
    """Compact serializer for recipes."""
    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class FollowSerializer(CustomUserSerializer):
    """Follow serializer."""
    recipes_count = SerializerMethodField()
    recipes = SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )

        read_only_fields = (
            'email',
            'username',
            'first_name',
            'last_name'
        )

    def validate(self, data):
        """Validate follow."""
        errors = {}
        following = self.instance
        user = self.context.get('request').user

        if Follow.objects.filter(following=following, user=user).exists():
            errors['re_sub'] = 'Нельзя подписаться повторно!'

        if user == following:
            errors['self_sub'] = 'Нельзя подписаться на самого себя!'

        if errors:
            raise ValidationError(errors)

        return data

    def get_is_subscribed(*args):
        return True

    def get_recipes(self, obj):
        """Get recipes with limitation."""
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = RecipeCompactSerializer(recipes, many=True, read_only=True)
        return serializer.data

    def get_recipes_count(self, obj):
        """Count recipes and get the number."""
        return obj.recipes.count()


class IngredientInRecipeSerializer(ModelSerializer):
    """Ingredient in recipe serializer."""
    id = IntegerField(write_only=True)

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class RecipeGetSerializer(ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = SerializerMethodField()
    image = Base64ImageField()
    is_favorited = SerializerMethodField(read_only=True)
    is_in_shopping_cart = SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_ingredients(self, obj):
        """Get ingredients."""
        ingredients = obj.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('ingredientinrecipe__amount')
        )

        return ingredients

    def get_is_favorited(self, obj):
        """Is recipe in favorite."""
        user = self.context['request'].user
        return (not user.is_anonymous and
                user.favorites.filter(recipe=obj).exists())

    def get_is_in_shopping_cart(self, obj):
        """Is recipe in shopping cart."""
        user = self.context['request'].user
        return (not user.is_anonymous and
                user.shopping_cart.filter(recipe=obj).exists())


class RecipeCreateSerializer(ModelSerializer):
    """Recipe serializer."""
    ingredients = IngredientInRecipeSerializer(many=True)
    tags = PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'name',
            'image',
            'text',
            'ingredients',
            'tags',
            'cooking_time'
        )

    def validate_tags(self, value):
        """Validate tags."""
        tags_set = set()
        errors = {}

        if not value:
            errors['no_tags'] = 'Нет тэгов! Добавьте хотя-бы один!'

        for tag in value:
            if tag in tags_set:
                errors['not_unique'] = 'Тэги не должны повторяться!'
            tags_set.add(tag)

        if errors:
            raise ValidationError(errors)

        return value

    def validate_ingredients(self, value):
        """Validate ingredients."""
        errors = {}

        if not value:
            errors['no_ingredients'] = ('Нет ингредиентов! '
                                        'Добавьте хотя-бы один!')

        ingredient_ids = set(Ingredient.objects.values_list('id', flat=True))
        ingredients_set = set()

        for item in value:
            if item['id'] not in ingredient_ids:
                errors['non_existent_ingredients'] = (
                    f"Ингредиенты не существуют: {item['id']}"
                )
            else:
                ingredient = get_object_or_404(Ingredient, id=item['id'])
                if ingredient in ingredients_set:
                    errors['duplicate_found'] = ('Ингридиенты не '
                                                 'должны повторяться!')
                if int(item['amount']) <= 0:
                    errors['amount'] = ('Количество ингредиента '
                                        'не должно быть 0!')
                ingredients_set.add(ingredient)

        if errors:
            raise ValidationError(errors)

        return value

    def fill_amount(self, ingredients, recipe):
        """Fill amount for the ingredient in the recipe."""
        ingredient_ids = [ingredient['id'] for ingredient in ingredients]
        ingredients_dict = {
            ingredient.id: ingredient
            for ingredient in Ingredient.objects.filter(id__in=ingredient_ids)
        }
        ingredients_amount = [
            IngredientInRecipe(
                ingredient=ingredients_dict[ingredient['id']],
                recipe=recipe,
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        IngredientInRecipe.objects.bulk_create(ingredients_amount)

    def create(self, validated_data):
        """Create method."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.fill_amount(recipe=recipe, ingredients=ingredients)

        return recipe

    def update(self, instance, validated_data):
        """Update method."""
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)
        instance = super().update(instance, validated_data)

        if ingredients is None or len(ingredients) == 0:
            raise ValidationError('Ингредиенты обязательны для обновления')

        if tags is None or len(tags) == 0:
            raise ValidationError('Теги обязательны для обновления')

        instance.ingredients.clear()
        self.fill_amount(recipe=instance, ingredients=ingredients)
        instance.tags.set(tags)
        instance.save()

        return instance

    def to_representation(self, instance):
        """Response presentation."""
        return RecipeGetSerializer(instance, context=self.context).data
