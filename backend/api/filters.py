from django_filters import rest_framework as filters
from recipes.models import Recipe, Tag
from rest_framework.filters import BaseFilterBackend

from .actions import common_filter_decorator


class IngredientsFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        name = request.query_params.get('name', None)
        search_method = request.query_params.get('search_method', 'startswith')

        if name:
            filter_kwargs = {
                f'name__i{search_method}': name
            }
            queryset = queryset.filter(**filter_kwargs)

        return queryset


class RecipeFilter(filters.FilterSet):

    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    @common_filter_decorator('Favorite')
    def filter_is_favorited(self, queryset, name, value):
        return queryset

    @common_filter_decorator('ShoppingCart')
    def filter_is_in_shopping_cart(self, queryset, name, value):
        return queryset

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart',
        )
