from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe, Tag


# Фильтр для ингредиентов
class IngredientSearchFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        fields = ('name', )
        model = Ingredient


# Фильтр для рецептов
class RecipeFilter(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug',
    )
    is_favorited = filters.BooleanFilter(method='get_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='get_is_in_shopping_cart'
    )

    class Meta:
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart',)
        model = Recipe

    # Метод для фильтрации по избранным
    def get_is_favorited(self, queryset, name, value):
        if value:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    # Метод для фильтрации по наличию в корзине покупок
    def get_is_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(shopping_carts__user=self.request.user)
        return queryset
