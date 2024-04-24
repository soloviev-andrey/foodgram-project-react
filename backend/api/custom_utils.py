from recipes.models import Favorite, ShoppingCart
from recipes.validators import DataValidationHelpers
from rest_framework import serializers


class RecipeIngredientsExtendedSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    measurement_unit = serializers.SerializerMethodField()
    amount = serializers.IntegerField()

    def get_id(self, instance):
        return instance.ingredient.id
    
    def get_name(self, instance):
        return instance.ingredient.name
    
    def get_measurement_unit(self, instance):
        return instance.ingredient.measurement_unit
  

class CustomRecipeFieldsSerializer(serializers.Serializer):
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_is_favorited(self, instance):
        return DataValidationHelpers.verify_recipe_relation(
            instance,
            self.context['request'].user,
            Favorite
        )

    def get_is_in_shopping_cart(self, instance):
        return DataValidationHelpers.verify_recipe_relation(
            instance,
            self.context['request'].user,
            ShoppingCart
        )


