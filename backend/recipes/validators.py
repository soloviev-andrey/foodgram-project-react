import re
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


def validate_color(value):
    '''Валидация HEX-значения цвета'''
    if not re.match(r'^#[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6}$', value):
        raise ValidationError('Введите корректное HEX-значение цвета')


class CustomTimeValidate(models.PositiveSmallIntegerField):
    def __init__(self, *args, **kwargs):
        kwargs['validators'] = [
            MinValueValidator(1, message='Даже мама не может так быстро готовить!'),
            MaxValueValidator(1440, message='Так может готовить только папа!'),
        ]
        super().__init__(*args, **kwargs)

    def validate(self, value, model_instance):
        super().validate(value, model_instance)
        if value < 1:
            raise ValidationError('Не менее одной минуты')
        if value > 1440:
            raise ValidationError('Не дольше 24 часов')

    def run_validators(self, value):
        super().run_validators(value)
        if value < 1:
            raise ValidationError('Не менее одной минуты')
        if value > 1440:
            raise ValidationError('Не дольше 24 часов')

