from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from users.serializers import ExtendedUserSerializer

from api.filters import IngredientsFilter, RecipeFilter
from api.pagination import LimitPageNumberPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (IngredientSerializer,
                             RecipeCreateUpdateSerializer, RecipeSerializer,
                             SnippetRecipeSerializer, SubscrimeSerializer,
                             TagSerializer)

from .decorators import (sf_action_decorator, subscribe_decorator,
                         subscriptions_decorator)
from .managers import RelatedObjectManager

CustomUser = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = [IngredientsFilter]


class CustomUserViewSet(UserViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = ExtendedUserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly,]

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticated,),
    )
    @subscribe_decorator(SubscrimeSerializer)
    def subscribe(self, request, sub_author=None):
        pass

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=(IsAuthenticated,),
    )
    @subscriptions_decorator
    def subscriptions(self, request):
        user = CustomUser.objects.all()
        data_source = user.filter(sub_fun__user=self.request.user)
        sub_serializer = SubscrimeSerializer(
            self.paginate_queryset(data_source),
            context={'request': request},
            many=True,
        )
        return self.get_paginated_response(sub_serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorOrReadOnly,]
    filter_backends = [DjangoFilterBackend,]
    pagination_class = LimitPageNumberPagination
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def create_object(self, request, model, recipe_id):
        try:
            recipe_unit = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            return Response(
                'Рецепт не найден',
                status.HTTP_400_BAD_REQUEST
            )
        existing_obj = model.objects.filter(
            user=request.user,
            recipe=recipe_unit
        ).first()
        if existing_obj:
            return Response(
                'Вы уже совершили это действие!',
                status=status.HTTP_400_BAD_REQUEST
            )
        new_obj = model(user=request.user, recipe=recipe_unit)
        new_obj.save()
        serializer = SnippetRecipeSerializer(
            recipe_unit,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_object(self, request, model, recipe_id):
        recipe_obj = get_object_or_404(Recipe, id=recipe_id)

        try:
            obj = model.objects.get(user=request.user, recipe=recipe_obj)
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except model.DoesNotExist:
            return Response(
                'Рецепт не найден в списке.',
                status=status.HTTP_400_BAD_REQUEST
            )

    @sf_action_decorator(ShoppingCart)
    def shopping_cart(self, request, pk=None):
        pass

    @sf_action_decorator(Favorite)
    def favorite(self, request, pk=None):
        pass

    @action(
        detail=False,
        methods=['GET'],
        url_path='download_shopping_cart',
        permission_classes=(IsAuthenticated,),
    )
    def generate_shopping_cart_file(self, request):
        uniq_ingredients = RelatedObjectManager.get_uniq_ingredients(
            request.user
        )
        shopcart_file_content = ''
        if uniq_ingredients:
            shopcart_file_content = '\n'.join(
                [(
                    f'{i["ingredient__name"]}'
                    f'- {i["total_amount"]}'
                    f'- {i["ingredient__measurement_unit"]}'
                ) for i in uniq_ingredients]
            )
            with open('shopping_cart.txt', 'w') as file:
                file.write(shopcart_file_content)
        print('Нет данных')
        return RelatedObjectManager.create_download_response(
            shopcart_file_content,
            'shopping-list.txt'
        )
