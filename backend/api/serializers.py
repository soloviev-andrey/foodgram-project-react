import base64
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import (
    serializers,
    validators,
)
from users.models import CustomUser, Subscrime
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



class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)

class CustomUserSerializer(UserSerializer):
    '''Сериализатор отображения пользователя'''
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed',
        )
    
    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if hasattr(request.user, 'email'):
                return Subscrime.objects.filter(
                    user=request.user,
                    author=obj.id
                ).exists()
        return False


class CustomUserCreateSerializer(UserCreateSerializer):
    '''Сериализатор регистрации и создания пользователя'''
    class Meta:
        model = CustomUser
        fields = (
            'id',
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
        )

class SubscrimeSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.ReadOnlyField(source='author.recipes.count')

    class Meta:
        model = CustomUser
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeCutSerializer(recipes, many=True).data
    
    @staticmethod
    def get_recipes_count(obj):
        return obj.recipes.count()
       
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
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class CreateUpdateIngredientsRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(write_only=True)
    amount = serializers.IntegerField(write_only=True)

    class Meta:
        model = IngredientsRecipe
        fields = ('id', 'amount',)

    def validate_amount(self, value):
        if value < 1 or value > 5000:
            raise serializers.ValidationError(
                'Кол-во должно быть от 1 до 5000!'
            )
        return value

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'amount',
        )

class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientsRecipeSerializer(
        many=True,
        source='recipe_ingredients'
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
        read_only_fields = ('is_favorited', 'is_in_shopping_cart',)

    def check_recipe(self, model, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return model.objects.filter(
            user=user,
            recipe=obj
            ).exists()

    def get_is_favorited(self, obj):
        return self.check_recipe(Favorite, obj)

    def get_is_in_shopping_cart(self, obj):
        return self.check_recipe(ShoppingCart, obj)


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    author = CustomUserSerializer(read_only=True)
    ingredients = CreateUpdateIngredientsRecipeSerializer(many=True, required=True)
    image = Base64ImageField(max_length=None, use_url=True)
    cooking_time = serializers.IntegerField(write_only=True)

    class Meta:
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
        model = Recipe
        validators = [
            validators.UniqueTogetherValidator(
                queryset=Recipe.objects.all(),
                fields=['name', 'text'],
                message='Такой рецепт уже существует!'
            )
        ]

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

    def create_tags_recipe(self, tags, recipe):
        for tag in tags:
            RecipeTag.objects.create(
                tag_id=tag.id,
                recipe=recipe
            )

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
        instance.tags.clear()
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
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



class FavoriteSerializer(RecipeCutSerializer):
    class Meta:
        model = Favorite
        fields = (
            'user',
            'recipe'
        )

    def to_representation(self, instance):
        return self.representation(
            self.context,
            instance.recipe,
            RecipeCutSerializer
        )

class ShoppingCartSerializer(RecipeCutSerializer):
    class Meta:
        model = ShoppingCart
        fields = (
            'user',
            'recipe'
        )

    def to_representation(self, instance):
        return self.representation(
            self.context,
            instance.recipe,
            RecipeCutSerializer
        )

    def representation(self, context, instance, serializer):
        request = context.get('request')
        new_context = {'request': request}
        return serializer(
            instance,
            context=new_context
        ).data