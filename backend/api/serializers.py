from django.contrib.auth import get_user_model
from recipes.models import Ingredient, IngredientsRecipe, Recipe, Tag
from recipes.validators import DataValidationHelpers
from rest_framework import serializers
from users.serializers import ExtendedUserSerializer
from users.utils import (BaseFielsSerializer, CustomRecipeFieldsSerializer,
                         ExtendedImageField,
                         RecipeIngredientsExtendedSerializer)

from .decorators import (recipe_create_decorator, recipe_update_decorator,
                         recipe_validate_decorator, recipes_decorator)
from .managers import RelatedObjectManager


class TagSerializer(BaseFielsSerializer):
    '''Сериализатор тэгов'''
    class Meta(BaseFielsSerializer.Meta):
        model = Tag


class IngredientSerializer(BaseFielsSerializer):
    '''Сериализатор ингредиентов'''
    class Meta(BaseFielsSerializer.Meta):
        model = Ingredient


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

    @recipe_validate_decorator
    def validate(self, value):
        return super().validate(value)

    @recipe_create_decorator
    def create(self, validated_data, author):
        return RelatedObjectManager.create_recipe(validated_data, author)

    @recipe_update_decorator
    def update(self, instance, validated_data):
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

    @recipes_decorator(SnippetRecipeSerializer)
    def get_recipes(self, instance, serialized_data):
        return serialized_data

    @recipes_decorator(SnippetRecipeSerializer)
    def get_recipes_count(self, instance, serializer):
        return instance.recipes.count()

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
