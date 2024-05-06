from functools import wraps

from recipes.models import IngredientsRecipe, RecipeTag
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db.models import Exists, OuterRef
from django.contrib.auth.models import AnonymousUser
from recipes.validators import DataValidationHelpers
from django.apps import apps


def customrecipefields_decorator(model):
    def decorator(func):
        @wraps(func)
        def wrapper(self, instance):
            return DataValidationHelpers.verify_recipe_relation(
                instance,
                self.context['request'].user,
                model
            )
        return wrapper
    return decorator


def filter_custom_decorator(model_name):
    def decorator(func):
        def wrapper(self, queryset, name, value):
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
        return wrapper
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
        def wrapper(self, request, pk=None):
            action = (
                self.create_object
                if request.method == 'POST'
                else self.delete_object
            )
            return action(request, model_class, pk)
        return wrapper
    return decorator


class BulkRelatedObjectCreator:

    def create_related_objects(self, objects, recipe, model, field_mapping):
        for obj in objects:
            data = {field_mapping[key]: value for key, value in obj.items()}
            data['recipe'] = recipe
            model.objects.create(**data)


class RelatedObjectManager:

    @staticmethod
    def create_tags(tags, recipe):
        tag_data = [{'tag_id': tag.id} for tag in tags]
        BulkRelatedObjectCreator().create_related_objects(
            tag_data,
            recipe,
            RecipeTag,
            {'tag_id': 'tag_id'}
        )

    @staticmethod
    def create_ingredients(ingredients, recipe):
        BulkRelatedObjectCreator().create_related_objects(
            ingredients,
            recipe,
            IngredientsRecipe,
            {'id': 'ingredient_id', 'amount': 'amount'}
        )

    @staticmethod
    def clear_related_fields(instance, field_name):
        related_field = getattr(instance, field_name)
        related_field.clear()
