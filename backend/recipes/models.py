from django.contrib.auth import get_user_model
from django.db import models
from .validators import BaseUnitValid, Valid_color

User = get_user_model()
MAX_LEN = 200
class Tag(models.Model):
    '''Модель тега'''

    name = models.CharField(
        'Название',
        max_length=MAX_LEN,
        unique=True,
    )
    color = models.CharField(
        'Цвет',
        max_length=MAX_LEN,
        unique=True,
        validators=[Valid_color],
    )
    slug = models.SlugField(
        'Уникальный слаг',
        max_length=MAX_LEN,
        unique=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.slug


class Ingredient(models.Model):
    '''Модель ингредиента'''

    name = models.CharField(
        'Наименование ингредиента',
        max_length=MAX_LEN,
    )
    measurement_unit = models.CharField(
        'Единицы измерения',
        max_length=MAX_LEN,
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
        max_length=MAX_LEN,
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
    cooking_time = BaseUnitValid(
        'Время приготовления в минутах'
    )
    pub_data = models.DateTimeField(
        'Время публикации',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class ListEntryModel(models.Model):
    '''Абстрактная модель'''
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
    )

    class Meta:
        abstract = True

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

class RecipeTag(models.Model):
    '''Промежудочная модель связи Recipe-Tag'''
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )

class IngredientsRecipe(models.Model):
    '''Промежуточную модель связи Ingredients-Recipe'''
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
    amount = BaseUnitValid(
        'Количество',
    )
