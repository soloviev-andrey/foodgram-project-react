from django.contrib import admin

from .models import Favorite, Ingredient, Recipe, ShoppingCart, Tag

admin.site.empty_value_display = 'Не задано'


class BaseFieldsAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display_links = ('name',)


class TagAdmin(BaseFieldsAdmin):
    list_display = ('name', 'color', 'slug')


class IngredientAdmin(BaseFieldsAdmin):
    list_display = (
        'name',
        'measurement_unit'
    )
    list_filter = ('name',)


class RecipeAdmin(BaseFieldsAdmin):
    list_display = ('name', 'author', 'total_count')
    list_filter = ('author', 'name', 'tags')

    def total_count(self, instance):
        return instance.favorite_set.count()
    total_count.short_description = 'Общее кол-во добавлений в избранное'


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
