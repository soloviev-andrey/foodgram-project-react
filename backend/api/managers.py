from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from recipes.models import IngredientsRecipe, Recipe, RecipeTag


class BulkRelatedObjectCreator:

    def create_related_objects(self, objects, recipe, model, field_mapping):
        related_objects = []

        for obj in objects:
            data = {field_mapping[key]: value for key, value in obj.items()}
            data['recipe'] = recipe
            related_objects.append(model(**data))
        model.objects.all().bulk_create(related_objects)


class RelatedObjectManager:

    @staticmethod
    def get_uniq_ingredients(user):
        uniq_ingredients = IngredientsRecipe.objects.filter(
            recipe__shoppingcart__user=user
        ).values('ingredient__name', 'ingredient__measurement_unit').annotate(
            total_amount=Coalesce(Sum('amount'), 0)
        )
        return uniq_ingredients

    @staticmethod
    def create_download_response(content, filename):
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @staticmethod
    def create_recipe(validated_data, author):
        return Recipe.objects.create(**validated_data, author=author)

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
