from django.apps import apps
from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    RegexValidator)
from django.db import models
from django.shortcuts import get_object_or_404

from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError

from .constant import MAX, MIN

Valid_color = RegexValidator(
    regex=r'^#[0-9A-Fa-f]{6}$',
    message='формат записи цвета -неправельный',
    code='invalid_color'
)


class UniqValidate:
    @staticmethod
    def validate_unique_objects(value, fields_name, model_name):
        objects = value.get(fields_name)
        if not objects:
            raise serializers.ValidationError(
                f'Не оставляйте поле {fields_name} пустым, добавьте элементы'
            )
        uniq_objects = set()
        for obj in objects:
            Model = apps.get_model('recipes', model_name)
            obj_id = obj.get('id') if model_name != 'Tag' else obj.id
            instance = get_object_or_404(Model, id=obj_id)
            if instance in uniq_objects:
                raise serializers.ValidationError(
                    'Добавлять одинаковые элементы запрещено'
                )
            uniq_objects.add(instance)
        return value


class BaseUnitValid(models.PositiveSmallIntegerField):
    def __init__(self, *args, **kwargs):
        # Добавляем валидаторы для поля
        kwargs['validators'] = [
            MinValueValidator(
                MIN,
                message='мало'
            ),
            MaxValueValidator(
                MAX,
                message='много'
            ),
        ]
        super().__init__(*args, **kwargs)


class DataValidationHelpers:

    @staticmethod
    def validate_tags(value):
        return UniqValidate.validate_unique_objects(value, 'tags', 'Tag')

    @staticmethod
    def validate_ingredients(value):
        return UniqValidate.validate_unique_objects(
            value,
            'ingredients',
            'Ingredient'
        )

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
    def create_relationships(self, items, model, recipe, **kwargs):
        for item in items:
            model.objects.create(recipe=recipe, **item, **kwargs)

    @staticmethod
    def subsribe_validate(self, data):
        request = self.context.get('request')
        sub_author_id = self.instance.id
        if sub_author_id == request.user.id:
            raise ValidationError('Вы не можете подписаться на самого себя.')
        return data
