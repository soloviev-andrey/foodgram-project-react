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


class CustomUserSerializer(UserSerializer):
    '''Сериализатор отображения пользователя'''
    is_subscribed = serializers.SerializerMethodField()

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
            return Subscrime.objects.filter(
                user=request.user,
                author=obj
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
    amount = serializers.IntegerField()
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientsRecipe
        fields = (
            'id',
            'name',
            'amount',
            'measurement_unit',
        )


class CreateUpdateIngredientsRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(
        validators=(
            MinValueValidator(
                1, message='Кол-во игредиентов должно от 1 и выше'
            ),
        )
    )

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'amount',
        )


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientsRecipeSerializer(
        many=True,
        source='recipe_ingredients'
    )
    image = Base64ImageField(required=False, allow_null=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def check_recipe(self, model, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return model.objects.filter(
            user=user,
            recipe=obj
        ).exists()

    def get_is_related(self, obj, model):
        return self.check_recipe(model, obj)

    def get_is_favorited(self, obj):
        return self.get_is_related(obj, Favorite)

    def get_is_in_shopping_cart(self, obj):
        return self.get_is_related(obj, ShoppingCart)

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


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = CreateUpdateIngredientsRecipeSerializer(
        many=True,
    )
    image = Base64ImageField(max_length=None, use_url=True)
    cooking_time = serializers.IntegerField(write_only=True)

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
        validators = [
            validators.UniqueTogetherValidator(
                queryset=Recipe.objects.all(),
                fields=['name', 'text'],
                message='Такой рецепт уже существует!'
            )
        ]

    def validate_cooking_time(self, value):
        '''Валидация времени готовки'''
        if value < 1 or value > 1000:
            raise serializers.ValidationError(
                'Пожалуйста, указывайте правильное время готовки!'
            )
        return value

    def validate(self, attrs):
        '''Дополнительная валидация'''
        ingredients = attrs.get('ingredients')
        tags = attrs.get('tags')
        if not ingredients:
            raise serializers.ValidationError(
                'Выберете хотя бы 1 ингредиент'
            )
        if not tags:
            raise serializers.ValidationError(
                'Нужно выбрать хотя бы 1 тег'
            )
        
        unique_rec = []
        for ingredient in ingredients:
            ing = get_object_or_404(
                Ingredient,
                id=ingredient.get('id'),
            )
            if ing in unique_rec:
                raise serializers.ValidationError(
                    'Не стоит добавлять один и тот же ингредиент много раз!'
                )
            unique_rec.append(ing)
        
        unique_tags = []
        for tag in tags:
            if tag in unique_tags:
                raise serializers.ValidationError(
                    'Не добавляйте один и тот же ингредиент много раз!'
                )
            unique_tags.append(tag)
        
        return attrs

    def create_tags_recipe(self, tags, recipe):
        '''Создание связей рецепта с тегами'''
        RecipeTag.objects.bulk_create([
            RecipeTag(tag_id=tag.id, recipe=recipe) for tag in tags
        ])

    def create_ingredients_recipe(self, ingredients, recipe):
        '''Создание связей рецепта с ингредиентами'''
        IngredientsRecipe.objects.bulk_create([
            IngredientsRecipe(
                ingredient_id=ingredient.get('id'),
                amount=ingredient.get('amount'),
                recipe=recipe
            ) for ingredient in ingredients
        ])

    def create(self, validated_data):
        '''Создание рецепта'''
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
        '''Обновление рецепта'''
        instance.tags.clear()
        IngredientsRecipe.objects.filter(recipe=instance).delete()
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
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


class SubscrimeSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='author.recipes.count')
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Subscrime
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

