import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.fields import IntegerField, SerializerMethodField
from rest_framework.serializers import (ImageField, ModelSerializer,
                                        PrimaryKeyRelatedField)

from recipes.models import Ingredient, IngredientInRecipe, Recipe, Tag
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
        return (
            user.is_authenticated
            and Follow.objects.filter(user=user, following=obj).exists()
        )


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
        following = self.instance
        user = self.context.get('request').user

        if Follow.objects.filter(following=following, user=user).exists():
            raise ValidationError('Нельзя подписаться повторно!')

        if user == following:
            raise ValidationError('Нельзя подписаться на самого себя!')

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
        serializer = RecipeCompactSerializer(
            recipes,
            many=True,
            read_only=True
        )
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

    def validate_amount(self, value):
        if int(value) <= 0:
            raise ValidationError(
                'Количество ингредиента не должно быть 0!'
            )
        return value


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
        return (
            user.is_authenticated
            and user.favorite_set.filter(recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        """Is recipe in shopping cart."""
        user = self.context['request'].user
        return (
            user.is_authenticated
            and user.shoppingcart_set.filter(recipe=obj).exists()
        )


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
        if not value:
            raise ValidationError('Нет тэгов! Добавьте хотя бы один!')

        if len(value) != len(set(value)):
            raise ValidationError('Тэги не должны повторяться!')

        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)

        ingredients = attrs.get('ingredients', [])

        if not ingredients:
            raise ValidationError('Нет ингредиентов! Добавьте хотя бы один!')

        ingredients_set = set()

        for item in ingredients:
            ingredient = get_object_or_404(Ingredient, id=item['id'])
            if ingredient in ingredients_set:
                raise ValidationError('Ингредиенты не должны повторяться!')
            ingredients_set.add(ingredient)

        return attrs

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

    @transaction.atomic
    def create(self, validated_data):
        """Create method."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.fill_amount(recipe=recipe, ingredients=ingredients)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update method."""
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)
        instance = super().update(instance, validated_data)

        instance.ingredients.clear()
        self.fill_amount(recipe=instance, ingredients=ingredients)
        instance.tags.set(tags)
        instance.save()

        return instance

    def to_representation(self, instance):
        """Response presentation."""
        return RecipeGetSerializer(instance, context=self.context).data
