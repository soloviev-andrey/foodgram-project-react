from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from django.contrib import admin

from .models import (Favorite, Ingredient, IngredientsRecipe, Recipe,
                     RecipeTag, ShoppingCart, Tag)


admin.site.empty_value_display = 'Не задано'


class BaseDeleteFormSet(BaseInlineFormSet):

    def clean(self):
        super().clean()
        for form in self.forms:
            if not hasattr(form, 'cleaned_data'):
                continue
            data = form.cleaned_data
            if data.get('DELETE'):
                raise ValidationError(
                    'Нельзя удалять все элементы даже в админке!'
                )


class BaseFieldsAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display_links = ('name',)


@admin.register(Tag)
class TagAdmin(BaseFieldsAdmin):
    list_display = ('name', 'color', 'slug')


class TagRecipeForm(BaseDeleteFormSet):
    pass


class TagRecipeInLine(admin.TabularInline):
    model = RecipeTag
    min_num = 1
    formset = TagRecipeForm


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit'
    )
    list_filter = ('name',)


class IngredientRecipeForm(BaseDeleteFormSet):
    pass


class IngredientRecipeInLine(admin.TabularInline):
    model = IngredientsRecipe
    min_num = 1
    formset = IngredientRecipeForm


@admin.register(Recipe)
class RecipeAdmin(BaseFieldsAdmin):
    list_display = ('name', 'author', 'total_count')
    list_filter = ('author', 'name', 'tags')
    search_fields = ('name',)
    inlines = (IngredientRecipeInLine, TagRecipeInLine)

    def total_count(self, instance):
        return instance.favorite_set.count()
    total_count.short_description = 'Общее кол-во добавлений в избранное'


admin.site.register(Favorite)
admin.site.register(ShoppingCart)
