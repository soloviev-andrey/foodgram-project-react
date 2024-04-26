from django.contrib.auth import get_user_model
from recipes.models import Ingredient, IngredientsRecipe, Recipe, Tag
from recipes.validators import DataValidationHelpers
from rest_framework import serializers
from users.models import Subscrime
from users.serializers import ExtendedUserSerializer

from .actions import RelatedObjectManager
from .custom_utils import (CustomRecipeFieldsSerializer,
                           RecipeIngredientsExtendedSerializer)
from .image_service import ExtendedImageField


class TagSerializer(serializers.ModelSerializer):
    '''Сериализатор тэгов'''
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    '''Сериализатор ингредиентов'''

    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientsRecipeSerializer(RecipeIngredientsExtendedSerializer):
    '''Сериализатор для вывода информация согласно тз'''
    class Meta:
        model = IngredientsRecipe
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )


class CreateIngredientsRecipeSerializer(serializers.ModelSerializer):
    '''Сериализатор добавления ингредиентов в рецепт'''
    id = serializers.IntegerField(
        validators=[
            DataValidationHelpers.validate_id
        ]
    )
    amount = serializers.IntegerField(
        validators=[
            DataValidationHelpers.validate_amount
        ]
    )

    class Meta:
        model = IngredientsRecipe
        fields = (
            'id',
            'amount',
        )


class RecipeSerializer(
    CustomRecipeFieldsSerializer,
    serializers.ModelSerializer
):
    '''Сериализатор рецепта'''
    ingredients = IngredientsRecipeSerializer(
        many=True,
        source='ingredients_recipe'
    )
    image = ExtendedImageField(
        valid_formats=['jpg', 'jpeg', 'png'],
        max_size=1024 * 1024
    )
    tags = TagSerializer(many=True)
    author = ExtendedUserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'text',
            'tags',
            'author',
            'cooking_time',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
        )


class SnippetRecipeSerializer(RecipeSerializer):

    class Meta(RecipeSerializer.Meta):
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    '''Сериализатор добавления и обновления рецепта'''
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    author = ExtendedUserSerializer(read_only=True)
    ingredients = CreateIngredientsRecipeSerializer(many=True)
    image = ExtendedImageField(
        valid_formats=['jpg', 'jpeg', 'png'],
        max_size=1024 * 1024
    )
    cooking_time = serializers.IntegerField(
        validators=[
            DataValidationHelpers.validate_cooking_time
        ]
    )

    def validate(self, value):
        value = DataValidationHelpers.validate_tags(value)
        value = DataValidationHelpers.validate_ingredients(value)
        return value

    def create(self, validated_data):
        author = self.context.get('request').user
        tags = validated_data.pop('tags') # noqa
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data, author=author)
        RelatedObjectManager.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        recipe_fields = {
            'tags': RelatedObjectManager.create_tags,
            'ingredients': RelatedObjectManager.create_ingredients,
        }
        for field, create_method in recipe_fields.items():
            if field in validated_data:
                RelatedObjectManager.clear_related_fields(instance, field)
                create_method(validated_data.pop(field), instance)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        serializer = RecipeSerializer(instance, context=self.context)
        return serializer.data

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )


class SubscrimeSerializer(ExtendedUserSerializer):
    '''Сериализатор для подписки пользователя'''
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    def get_recipes(self, instance):

        recipes_request = self.context.get('request')
        limit_term = recipes_request.query_params.get('recipes_limit', None)
        recipes = instance.recipes.all()

        if limit_term:
            try:
                limit = int(limit_term)
                if limit > 0:
                    recipes = recipes[:limit]
            except ValueError:
                pass
        serialized_recipes = SnippetRecipeSerializer(
            recipes,
            many=True,
            context={'request': recipes_request}
        )
        return serialized_recipes.data

    def get_recipes_count(self, instance):
        return instance.recipes.count()

    def get_is_subscribed(self, instance):
        user_request = self.context.get('request')
        if user_request.user.is_anonymous:
            return False

        user_subscribed = Subscrime.objects.filter(
            user=user_request.user,
            author=instance,
        ).exists()
        return user_subscribed

    class Meta:
        model = get_user_model()
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )
