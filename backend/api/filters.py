from django.db.models import Exists, OuterRef
from django_filters import rest_framework as filters
from recipes.models import Favorite, Recipe, ShoppingCart, Tag
from django.contrib.auth.models import AnonymousUser

class RecipeFilter(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if isinstance(user, AnonymousUser):
            return queryset.none()
        
        return queryset.annotate(
            Favorite=Exists(Favorite.objects.filter(user=user, recipe_id=OuterRef('id')))
        ).filter(Favorite=value)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if isinstance(user, AnonymousUser):
            return queryset.none()
        
        return queryset.annotate(
            ShopCart=Exists(ShoppingCart.objects.filter(user=user, recipe_id=OuterRef('id')))
        ).filter(ShopCart=value)

    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart'
        )

