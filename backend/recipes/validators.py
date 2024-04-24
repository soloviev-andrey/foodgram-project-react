from django.apps import apps
from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    RegexValidator)
from django.db import models
from rest_framework import serializers, status

from .constant import MAX, MIN

Valid_color = RegexValidator(
    regex=r'^#[0-9A-Fa-f]{6}$',
    message='формат записи цвета -неправельный',
    code='invalid_color'
)

class BaseUnitValid(models.PositiveSmallIntegerField):
    def __init__(self, *args, **kwargs):
        # Добавляем валидаторы для поля
        kwargs['validators'] = [
            MinValueValidator(
                MIN,
                message='мало'
            ),
            MaxValueValidator(MAX, message='много'),
        ]
        super().__init__(*args, **kwargs)

class DataValidationHelpers:
    
    @staticmethod
    def verify_recipe_relation(obj, user, model):
        if user.is_authenticated:
            return model.objects.filter(user=user, recipe=obj).exists()
        return False

    @staticmethod
    def validate_id(value):
        Ingredient = apps.get_model('recipes', 'Ingredient')
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                'Ингредиент с таким ID не существует!',
                code=status.HTTP_400_BAD_REQUEST
            )
        return value

    @staticmethod
    def validate_amount(value):
        if not MIN <= value <= MAX:
            raise serializers.ValidationError(
                'Кол-во должно быть от 1 до 5000!'
            )
        return value

    @staticmethod
    def validate_cooking_time(value):
        if not MIN <= value <= MAX:
            raise serializers.ValidationError(
                'Пожалуйста, указывайте адекватное время готовки!'
            )
        return value

    @staticmethod
    def validate_tags(value):
        unique_tags = []
        if not value:
            raise serializers.ValidationError(
                'Нужно выбрать хотя бы 1 тег!',
                code='required'
            )
        for tag in value:
            if tag in unique_tags:
                raise serializers.ValidationError(
                    'Не стоит добавлять один и тот же тэг!'
                )
            unique_tags.append(tag)
        return value
