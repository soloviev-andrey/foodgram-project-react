import re
from django.core.exceptions import ValidationError


def validate_color(value):
    '''Валидация HEX-значения цвета'''
    if not re.match(r'^#[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6}$', value):
        raise ValidationError('Введите корректное HEX-значение цвета')
