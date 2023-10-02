import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.validators import RegexValidator
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import status, serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer

from recipes.models import Tag, Ingredient, Recipe
from users.models import User, Follow

User = get_user_model()


class CustomUserSerializer(UserSerializer):
    """Custom user serializer."""
    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed',)

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user

        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, following=obj).exists()


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

    def validate_username(self, value):
        """Validate username."""
        validator = RegexValidator(
            r'^[\w.@+-]+$',
            message='Используй буквы, цифры, _ . @ + -'
        )
        validator(value)

        return value


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


class Base64ImageField(serializers.ImageField):
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
    recipes = RecipeCompactSerializer(many=True, read_only=True)

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
            raise ValidationError(
                detail='Нельзя подписаться повторно!',
                code=status.HTTP_400_BAD_REQUEST
            )
        if user == following:
            raise ValidationError(
                detail='Нельзя подписаться на самого себя!',
                code=status.HTTP_400_BAD_REQUEST
            )
        return data

    def get_is_subscribed(*args) -> bool:
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
