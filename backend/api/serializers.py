import base64
from rest_framework.response import Response
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework import (
    serializers,
    validators,
    status,
)
from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import AuthenticationFailed
from users.models import Subscrime
from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
from recipes.models import (
    Favorite,
    IngredientsRecipe,
    RecipeTag,
    ShoppingCart,
    Tag,
    Ingredient,
    Recipe,
)
from djoser.serializers import UserCreateSerializer, UserSerializer
from django.contrib.auth import get_user_model

# -----------------------------------------------------------------------------
#                            Users
# -----------------------------------------------------------------------------

User = get_user_model()
class CustomUserSerializer(UserSerializer):
    '''Сериализатор отображения пользователя'''
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed',
        )
    
    def to_representation(self, instance):
        if isinstance(instance, AnonymousUser):
            raise AuthenticationFailed(
                detail='Неавторизованный пользователь'
            )
        return super().to_representation(instance)
    
    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_staff:
            return Subscrime.objects.filter(user=request.user, author=obj).exists()
        return False


class CustomUserCreateSerializer(UserCreateSerializer):
    '''Сериализатор регистрации и создания пользователя'''
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
        )

class SubscrimeSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
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

    def get_recipes(self, obj):
        recipes_limit = self.context.get(
            'request'
            ).query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeCutSerializer(recipes, many=True).data

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return Subscrime.objects.filter(
            user=user,
            author=obj
            ).exists()

    def get_recipes_count(self, obj):
        return obj.recipes.count()
    

# -----------------------------------------------------------------------------
#                            Recipes
# -----------------------------------------------------------------------------

class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)
 
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

class IngredientsRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientsRecipe
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )


class CreateIngredientsRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(write_only=True)
    amount = serializers.IntegerField(write_only=True)

    class Meta:
        model = IngredientsRecipe
        fields = (
            'id',
            'amount',
        )

    def validate_id(self, value):
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                'Ингредиент с таким ID не существует!',
                code=status.HTTP_400_BAD_REQUEST
            )
        return value

    def validate_amount(self, value):
        if value < 1 or value > 5000:
            raise serializers.ValidationError(
                'Кол-во должно быть от 1 до 5000!'
            )
        return value

class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientsRecipeSerializer(
        many=True,
        source='ingredients_recipe',
    )
    image = Base64ImageField(required=False, allow_null=True)
    tags = TagSerializer(many=True)
    author = CustomUserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

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
        read_only_fields = (
            'is_favorited',
            'is_in_shopping_cart',
        )
    
    def get_is_recipe_relation(self, obj, model):
        user = self.context['request'].user
        if user.is_authenticated:
            return model.objects.filter(user=user, recipe=obj).exists()
        return False

    def get_is_favorited(self, obj):
        return self.get_is_recipe_relation(obj, Favorite)

    def get_is_in_shopping_cart(self, obj):
        return self.get_is_recipe_relation(obj, ShoppingCart)

class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    author = CustomUserSerializer(read_only=True)
    ingredients = CreateIngredientsRecipeSerializer(many=True)
    image = Base64ImageField(max_length=None, use_url=True)
    cooking_time = serializers.IntegerField()

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


    def validate_cooking_time(self, value):
        if value < 1 or value > 5000:
            raise serializers.ValidationError(
                'Пожалуйста, указывайте адекватное время готовки!'
            )
        return value

    def validate(self, attrs):
        ingredients = attrs.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                'Нужно выбрать хотя бы 1 ингредиент!'
            )
        unique_ings = []
        for ingredient in ingredients:
            ing = get_object_or_404(Ingredient, id=ingredient.get('id'))
            if ing in unique_ings:
                raise serializers.ValidationError(
                    'Не стоит добавлять один и тот же ингредиент много раз!'
                )
            unique_ings.append(ing)
        return attrs

    def create_tags_recipe(self, tags, recipe):
        for tag in tags:
            RecipeTag.objects.create(
                tag_id=tag.id,
                recipe=recipe
            )
    
    def validate_tags(self, tags):
        unique_tags = []
        if not tags:
            raise serializers.ValidationError(
                'Нужно выбрать хотя бы 1 тег!'
            )
        for tag in tags:
            if tag in unique_tags:
                raise serializers.ValidationError(
                    'Не стоит добавлять один и тот же ингредиент много раз!'
                )
            unique_tags.append(tag)
        return tags

    def create_ingredients_recipe(self, ingredients, recipe):
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
            self.create_ingredients_recipe(ingredients, recipe)
            self.create_tags_recipe(tags, recipe)
            return recipe
        except IntegrityError:
            raise serializers.ValidationError(
                'Такой рецепт уже существует!'
            )

    def update(self, instance, validated_data):
        if 'tags' not in validated_data:
           raise serializers.ValidationError(
               'Поле "tags" обязательно для обновления рецепта.',
               code='required'
           )
    
        tags = validated_data.pop('tags')
        instance.tags.clear()
        ingredients = validated_data.pop('ingredients', [])

        IngredientsRecipe.objects.filter(recipe=instance).delete()
        self.create_ingredients_recipe(ingredients, instance)
        self.create_tags_recipe(tags, instance)
        super().update(instance, validated_data)
        return instance


class RecipeCutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )