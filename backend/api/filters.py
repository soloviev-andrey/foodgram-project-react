from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django_filters import rest_framework as filters
from recipes.models import Ingredient, Recipe, Tag

User = get_user_model()

class IngredientNameFilter(filters.FilterSet):

    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = (
            'name',
            'measurement_unit',
        )


class RecipeFilter(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart'
        )

    def filter_is_favorited(self, queryset, name, value):
        if not isinstance(self.request.user, AnonymousUser):
            user = self.request.user
            if value:
                return queryset.filter(favorites__user=user)
            else:
                return queryset.exclude(favorites__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if not isinstance(self.request.user, AnonymousUser):
            user = self.request.user
            if value:
                return queryset.filter(shopping_cart__user=user)
            else:
                return queryset.exclude(shopping_cart__user=user)
        return queryset
