from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from .custom_fields import CustomRecipeFieldsSerializer, RecipeIngredientsExtendedSerializer
from recipes.validators import DataValidationHelpers
from .image_service import ExtendedImageField
from users.serializers import ExtendedUserSerializer
from recipes.models import (Ingredient, IngredientsRecipe, Recipe,
                            RecipeTag, Tag)
from rest_framework import serializers
from users.models import Subscrime

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

class RecipeSerializer(CustomRecipeFieldsSerializer, serializers.ModelSerializer):
    '''Сериализатор рецепта'''
    ingredients = IngredientsRecipeSerializer(
        many=True,
        source = 'ingredients_recipe'
    )
    image = ExtendedImageField(
        valid_formats=['jpg', 'jpeg', 'png'],
        max_size=1024*1024
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
        max_size=1024*1024
    )
    cooking_time = serializers.IntegerField(
        validators=[
            DataValidationHelpers.validate_cooking_time
        ]
    )
    
    def validate(self, attrs):
        ingredients = attrs.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                'Не оставляйте поле пустым, добавьте ингредиент'
            )
        uniq_ings = set()
        for ingredient in ingredients:
            ing = get_object_or_404(
                Ingredient,
                id=ingredient.get('id')
            )
            if ing in uniq_ings:
                raise serializers.ValidationError(
                    'Добавлять одинаковые элементы запрещено'
                )
            uniq_ings.add(ing)
        return attrs

    def create_tags(self, tags, recipe):
        for tag in tags:
            RecipeTag.objects.create(
                tag_id=tag.id,
                recipe=recipe
            )

    def create_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            IngredientsRecipe.objects.create(
                ingredient_id=ingredient.get('id'),
                amount=ingredient.get('amount'),
                recipe=recipe
            )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        author = self.context.get('request').user
        
        try:
            recipe = Recipe.objects.create(**validated_data, author=author)
            self.create_ingredients(ingredients, recipe)
            return recipe
        except IntegrityError:
            raise serializers.ValidationError(
                'Такой рецепт уже существует!'
            )
    
    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Нужно выбрать хотя бы 1 тег!', code='required'
            )
        
        unique_tags = set()
        for tag in value:
            if tag in unique_tags:
                raise serializers.ValidationError(
                    'Не стоит добавлять один и тот же тэг!'
                )
            unique_tags.add(tag)
        
        return value

    def update(self, instance, validated_data):
        if 'tags' not in validated_data:
            raise serializers.ValidationError(
                'Поле "tags" обязательно для обновления рецепта.'
            )
        tags = validated_data.pop('tags')
        instance.tags.clear()
        ingredients = validated_data.pop('ingredients', [])
        IngredientsRecipe.objects.filter(recipe=instance).delete()
        self.create_ingredients(ingredients, instance)
        self.create_tags(tags, instance)
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
