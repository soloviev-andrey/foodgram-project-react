from django.db import models

from .constant import MAX_LEN, User
from .validators import BaseUnitValid, Valid_color


class Tag(models.Model):
    """Модель тега"""

    name = models.CharField(
        'Название',
        max_length=MAX_LEN,
        unique=True,
        blank=False,
    )
    color = models.CharField(
        'Цвет',
        max_length=MAX_LEN,
        unique=True,
        blank=False,
        validators=[Valid_color],
    )
    slug = models.SlugField(
        'Уникальный слаг',
        max_length=MAX_LEN,
        blank=False,
        unique=True,
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента"""

    name = models.CharField(
        'Наименование ингредиента',
        max_length=MAX_LEN,
        blank=False,
    )
    measurement_unit = models.CharField(
        'Единицы измерения',
        max_length=MAX_LEN,
        blank=False,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name} - {self.measurement_unit}'


class Recipe(models.Model):
    """Модель рецепта"""
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        verbose_name='Теги рецепта',
        blank=False
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор публикации (пользователь)',
        blank=False
    )
    name = models.CharField(
        'Название',
        max_length=MAX_LEN,
        blank=False
    )
    image = models.ImageField(
        'Картинка рецепта',
        upload_to='recipes/images/',
        blank=False
    )
    text = models.TextField(
        'Текстовое описание',
        blank=False
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientsRecipe',
        verbose_name='Ингредиенты',
        blank=False
    )
    cooking_time = BaseUnitValid(
        'Время приготовления в минутах',
        blank=False
    )
    pub_data = models.DateTimeField(
        'Время публикации',
        auto_now_add=True,
        blank=False
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_data', ]

    def __str__(self):
        return self.name


class ListEntryModel(models.Model):
    """Абстрактная модель"""
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

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class Favorite(ListEntryModel):
    """Модель для Избранное"""
    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return f'Рецепт {self.recipe} в избранном у пользователя {self.user}'


class ShoppingCart(ListEntryModel):
    """Модель для списка покупок"""

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'

    def __str__(self):
        return (
            f'{self.recipe} у пользователя {self.user} в списке покупок'
        )


class RecipeTag(models.Model):
    """Промежудочная модель связи Recipe-Tag"""
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тег'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return f'{self.tag} - {self.recipe}'


class IngredientsRecipe(models.Model):
    """Промежуточную модель связи Ingredients-Recipe"""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='ingredients_recipe'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
    )
    amount = BaseUnitValid(
        'Количество',
    )

    class Meta:
        verbose_name = 'ингредиент в рецепт'
        verbose_name_plural = 'Кол-во ингредиентов в рецепте'

    def __str__(self):
        return f'{self.ingredient} - {self.recipe}'
