from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.core.validators import RegexValidator

Valid_color = RegexValidator(
    regex=r'^#[0-9A-Fa-f]{6}$',
    message='Введите корректный цвет в формате HEX (например, #RRGGBB).',
    code='invalid_color'
)

class BaseUnitValid(models.PositiveSmallIntegerField):
    def __init__(self, *args, **kwargs):
        # Добавляем валидаторы для поля
        kwargs['validators'] = [
            MinValueValidator(
                1,
                message='невозможно так быстро'
            ),
            MaxValueValidator(1440, message='очень долго'),
        ]
        super().__init__(*args, **kwargs)
