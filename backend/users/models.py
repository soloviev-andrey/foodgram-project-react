from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    '''Модель Пользователя'''
    email = models.EmailField(
        'Электронная почта',
        max_length=254,
        unique=True
        )
    username = models.CharField(
        'НИК пользователя',
        max_length=200,
        unique=True
        )
    first_name = models.CharField(
        'Имя',
        max_length=200
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=200
    )
    password = models.CharField(
        'Пароль',
        max_length=200
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def str(self):
        return self.username


class Subscrime(models.Model):
    '''Модель подписки'''

    users = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self) -> str:
        return f'{self.user} подписан на {self.author}'

