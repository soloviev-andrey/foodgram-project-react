from django.db.models import Exists, OuterRef
from django_filters import rest_framework as filters
from recipes.models import Recipe, Tag
from django.contrib.auth.models import AnonymousUser
from django.apps import apps

class RecipeFilter(filters.FilterSet):

    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_is_in_shopping_cart')


    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        favorite=apps.get_model('recipes', 'Favorite')
        if isinstance(user, AnonymousUser):
            return queryset
        
        return queryset.annotate(
            Favorite=Exists(favorite.objects.filter(user=user, recipe_id=OuterRef('id')))
        ).filter(Favorite=value)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        shopcart = apps.get_model('recipes', 'ShoppingCart')
        if isinstance(user, AnonymousUser):
            return queryset
        
        return queryset.annotate(
            ShopCart=Exists(shopcart.objects.filter(user=user, recipe_id=OuterRef('id')))
        ).filter(ShopCart=value)


    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart',
        )

