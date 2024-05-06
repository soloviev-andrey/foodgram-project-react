from functools import wraps

from recipes.constant import User
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db.models import Exists, OuterRef
from django.contrib.auth.models import AnonymousUser
from recipes.validators import DataValidationHelpers
from django.apps import apps
from rest_framework.response import Response
from rest_framework import status


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
