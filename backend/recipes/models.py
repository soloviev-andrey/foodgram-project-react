from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from recipes.validators import CustomTimeValidate, validate_color

User = get_user_model()

class ListEntryModel(models.Model):
    '''Абстрактная модель'''
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True

class Tag(models.Model):
    '''Модель тега'''

    name = models.CharField(
        'Название',
        max_length=30,
        unique=True,
    )
    color = models.CharField(
        'Цвет',
        max_length=7,
        unique=True,
        validators=[
            validate_color,
        ],
    )
    slug = models.SlugField(
        'Уникальный слаг',
        max_length=200,
        unique=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.slug[:15]


class Ingredient(models.Model):
    '''Модель ингредиента'''

    name = models.CharField(
        'Наименование ингредиента',
        max_length=200,
    )
    measurement_unit = models.CharField(
        'Единицы измерения',
        max_length=200,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name} - {self.measurement_unit}'


class Recipe(models.Model):
    '''Модель рецепта'''
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        verbose_name='Теги рецепта',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор публикации (пользователь)',
    )
    name = models.CharField(
        'Название',
        max_length=200,
    )
    image = models.ImageField(
        'Картинка рецепта',
        upload_to='recipes/images/',
    )
    text = models.TextField(
        'Текстовое описание',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientsRecipe',
        verbose_name='Ингредиенты',
    )
    cooking_time = CustomTimeValidate(
        'Время приготовления в минутах'
    )
    pub_data = models.DateTimeField(
        'Время публикации',
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_data',)

    def __str__(self):
        return self.name


class IngredientsRecipe(models.Model):
    '''Промежуточную модель - IngredientsRecipe'''
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='ingredients_recipe',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[MinValueValidator(1)],
    )

    class Meta:
        verbose_name = 'Связь ингредиента и рецепта'
        verbose_name_plural = 'Связь ингредиентов и рецептов'

    def __str__(self):
        return f'{self.ingredient} входит в основу {self.recipe}'


class RecipeTag(models.Model):
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тег',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Теги'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return f'Для рецепта {self.recipe} есть таг{self.tag}'


class Favorite(ListEntryModel):
    '''Модель для Избранное'''
    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        

    def __str__(self):
        return f'Рецепт {self.recipe} в избранном у пользователя {self.user}'


class ShoppingCart(ListEntryModel):
    '''Модель для списка покупок'''

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'

    def __str__(self):
        return (
            f'{self.recipe} у пользователя {self.user} в списке покупок'
        )
