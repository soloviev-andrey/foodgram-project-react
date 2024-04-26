from recipes.models import IngredientsRecipe, RecipeTag


class SerializerCreateUtils:
     def create_related_objects(self, objects, recipe, model, field_mapping):
        for obj in objects:
            data = {field_mapping[key]: value for key, value in obj.items()}
            data['recipe'] = recipe
            model.objects.create(**data)

class CreateSerializer:

    @staticmethod
    def create_tags(tags, recipe):
        tag_data = [{'tag_id': tag.id} for tag in tags]
        SerializerCreateUtils().create_related_objects(
            tag_data,
            recipe,
            RecipeTag,
            {'tag_id': 'tag_id'}
        )

    @staticmethod
    def create_ingredients(ingredients, recipe):
        SerializerCreateUtils().create_related_objects(
            ingredients,
            recipe,
            IngredientsRecipe,
            {'id': 'ingredient_id', 'amount': 'amount'}
        )