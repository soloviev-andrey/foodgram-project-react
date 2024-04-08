from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

MAX_LENGTH = 150
EMAIL_LENGTH = 254


class CustomUser(AbstractUser):
    '''Модель Пользователя'''
    username = models.CharField(
        'НИК пользователя',
        max_length=MAX_LENGTH,
        unique=True,
        blank=False,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message='Некорректное имя',
            )
        ],
    )
    first_name = models.CharField(
        'Имя',
        max_length=MAX_LENGTH,
        blank=False,
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=MAX_LENGTH,
        blank=False,
    )
    email = models.EmailField(
        'Электронная почта',
        max_length=EMAIL_LENGTH,
        unique=True,
    )
    password = models.CharField(
        'Пароль',
        max_length=MAX_LENGTH,
        blank=False,
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        '''Устанавливаем права пользователя перед сохранением.'''
        if self.is_superuser:
            self.is_staff = True
        else:
            self.is_staff = False
            self.is_superuser = False
        super().save(*args, **kwargs)


class Subscrime(models.Model):
    '''Модель подписки'''

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='author',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

        constraints = [
            models.UniqueConstraint(fields=['user', 'author'],
                                    name='unique_subscriber'),
        ]

    def __str__(self) -> str:
        return f'{self.user} подписан на {self.author}'
