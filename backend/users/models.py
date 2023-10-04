from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import UniqueConstraint

LENGTH_LARGE = 254
LENGTH_MEDIUM = 150


class User(AbstractUser):
    """Custom user model."""
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username',
        'first_name',
        'last_name',
        'password',
    )
    username = models.CharField(
        verbose_name='Никнейм',
        max_length=LENGTH_MEDIUM,
        unique=True
    )
    email = models.EmailField(
        verbose_name='Email',
        max_length=LENGTH_LARGE,
        unique=True
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=LENGTH_MEDIUM
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=LENGTH_MEDIUM
    )
    password = models.CharField(
        verbose_name="Пароль",
        max_length=LENGTH_MEDIUM
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        """String representation."""
        return self.username


class Follow(models.Model):
    """Follow model."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Подписан',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки',

        constraints = [
            UniqueConstraint(
                name='unique_follow',
                fields=['user', 'following'],
            )
        ]

    def __str__(self):
        """String representation."""
        return f'{self.user.username} -> {self.following.username}'

    def clean(self):
        super().clean()

        if self.user == self.following:
            raise ValidationError('Нельзя подписаться на самого себя')
