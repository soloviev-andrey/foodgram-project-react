from django.contrib import admin
from .models import (
    Tag,
    Ingredient,
    Recipe,
    IngredientsRecipe,
    Favorite,
    ShoppingCart
)

admin.site.empty_value_display = 'Не задано'


class IngredientAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'measurement_unit'
    )

    list_filter = ('name',)


class RecipeAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'author'
    )
    list_filter = (
        'author',
        'name',
        'tags'
    )


admin.site.register(Tag)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(IngredientsRecipe)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)


# Register your models here.
