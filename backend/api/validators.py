from recipes.models import Ingredient
from rest_framework import serializers, status

class DataValidationHelpers:
    
    @staticmethod
    def verify_recipe_relation(obj, user, model):
        if user.is_authenticated:
            return model.objects.filter(user=user, recipe=obj).exists()
        return False

    @staticmethod
    def validate_id(value):
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                'Ингредиент с таким ID не существует!',
                code=status.HTTP_400_BAD_REQUEST
            )
        return value

    @staticmethod
    def validate_amount(value):
        if value < 1 or value > 5000:
            raise serializers.ValidationError(
                'Кол-во должно быть от 1 до 5000!'
            )
        return value

    @staticmethod
    def validate_cooking_time(value):
        if not 1 <= value <= 5000:
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
