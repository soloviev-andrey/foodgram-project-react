from django.contrib.auth.models import AbstractUser
from django.db import models
from recipes.validators import valid_name


MAX_LEN = 150
EMAIL_LEN = 254
class CustomUser(AbstractUser):
    '''Модель Пользователя'''
    username = models.CharField(
        'НИК пользователя',
        max_length=MAX_LEN,
        unique=True,
        blank=False,
        validators=[valid_name],
    )
    first_name = models.CharField(
        'Имя',
        max_length=MAX_LEN,
        blank=False,
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=MAX_LEN,
        blank=False,
    )
    email = models.EmailField(
        'Электронная почта',
        max_length=EMAIL_LEN,
        unique=True,
    )
    password = models.CharField(
        'Пароль',
        max_length=MAX_LEN,
        blank=False,
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username

class Subscrime(models.Model):
    '''Модель подписки'''

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='sub_fun',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self) -> str:
        return f'{self.user} подписан на {self.author}'
