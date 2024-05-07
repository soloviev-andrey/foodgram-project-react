from functools import wraps

from django.apps import apps
from django.contrib.auth.models import AnonymousUser
from django.db.models import Exists, OuterRef
from recipes.constant import User
from recipes.validators import DataValidationHelpers
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .managers import RelatedObjectManager


def recipes_decorator(serializer):
    def decorator(func):
        @wraps(func)
        def handler(self, instance):
            request = self.context.get('request')
            limit = int(request.query_params.get('recipes_limit', 0))

            recipes = (
                instance.recipes.all()[:limit]
                if limit > 0
                else instance.recipes.all()
            )
            serialized_recipes = serializer(
                recipes,
                many=True,
                context={'request': request}
            )
            return func(self, instance, serialized_recipes.data)
        return handler
    return decorator


def recipe_validate_decorator(func):
    def handler(self, value):
        value = DataValidationHelpers.validate_tags(value)
        value = DataValidationHelpers.validate_ingredients(value)
        return func(self, value)
    return handler


def recipe_update_decorator(func):
    def handler(self, instance, validated_data):
        recipe_fields = {
            'tags': RelatedObjectManager.create_tags,
            'ingredients': RelatedObjectManager.create_ingredients,
        }
        for field, create_method in recipe_fields.items():
            if field in validated_data:
                RelatedObjectManager.clear_related_fields(instance, field)
                create_method(validated_data.pop(field), instance)
        return func(self, instance, validated_data)
    return handler


def recipe_create_decorator(func):
    def handler(self, validated_data):
        tags = validated_data.pop('tags')
        author = self.context.get('request').user
        ingredients = validated_data.pop('ingredients')
        recipe = func(self, validated_data, author)
        RelatedObjectManager.create_tags(tags, recipe)
        RelatedObjectManager.create_ingredients(ingredients, recipe)
        return recipe
    return handler


def user_auth_decorator(view_func):
    def handler(self, instance):
        if isinstance(instance, AnonymousUser):
            raise AuthenticationFailed('Неавторизованный пользователь')
        return view_func(self, instance)
    return handler


def subscribed_decorator(view_func):
    def handler(self, target):
        return (
            self.context['request'].user.is_staff
            and target.subscrime.exists()
        )
    return handler


def get_field_decorator(field_name):
    def decorator(self, instance):
        return getattr(instance.ingredient, field_name)
    return decorator


def subscriptions_decorator(func):
    @wraps(func)
    def handler(self, request, *args, **kwargs):
        user = User.objects.all()
        data_source = user.filter(sub_fun__user=self.request.user)

        if not data_source.exists():
            return Response(
                {'Вы не подписались ни на кого'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return func(self, request, *args, **kwargs)
    return handler


def customrecipefields_decorator(model):
    def decorator(func):
        @wraps(func)
        def handler(self, instance):
            return DataValidationHelpers.verify_recipe_relation(
                instance,
                self.context['request'].user,
                model
            )
        return handler
    return decorator


def filter_custom_decorator(model_name):
    def decorator(func):
        def handler(self, queryset, name, value):
            user = self.request.user
            model = apps.get_model('recipes', model_name)
            if isinstance(user, AnonymousUser):
                return queryset
            return queryset.annotate(
                CustomFilter=Exists(
                    model.objects.filter(
                        user=user,
                        recipe_id=OuterRef('id')
                    )
                )
            ).filter(CustomFilter=value)
        return handler
    return decorator


def sf_action_decorator(
        model_class,
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
):
    def decorator(view_func):
        @action(
            detail=detail,
            methods=methods,
            permission_classes=permission_classes
        )
        @wraps(view_func)
        def handler(self, request, pk=None):
            action = (
                self.create_object
                if request.method == 'POST'
                else self.delete_object
            )
            return action(request, model_class, pk)
        return handler
    return decorator
