from collections import defaultdict

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from .decorators import sf_action_decorator
from recipes.models import (Favorite, Ingredient, IngredientsRecipe, Recipe,
                            ShoppingCart, Tag)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from users.models import Subscrime
from users.serializers import ExtendedUserSerializer

from api.filters import IngredientsFilter, RecipeFilter
from api.pagination import LimitPageNumberPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (IngredientSerializer,
                             RecipeCreateUpdateSerializer, RecipeSerializer,
                             SnippetRecipeSerializer, SubscrimeSerializer,
                             TagSerializer)

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
    def subscribe(self, request, **kwargs):

        sub_aut = get_object_or_404(CustomUser, id=self.kwargs.get('id'))
        if sub_aut == self.request.user:
            return Response(
                'Вам отказано в данном действии',
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.method == 'POST':
            sub_instanse, new_creat = Subscrime.objects.get_or_create(
                user=request.user, author=sub_aut
            )
            if not new_creat:
                return Response(
                    'Уже есть подписка на данного автора',
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = SubscrimeSerializer(
                sub_aut,
                context={'request': request}
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        if request.method == 'DELETE':
            try:
                sub_instanse = Subscrime.objects.get(
                    user=request.user,
                    author=sub_aut
                )
                sub_instanse.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Subscrime.DoesNotExist:
                return Response(
                    'Подписка не существует, или еще не создана',
                    status=status.HTTP_400_BAD_REQUEST
                )

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        user = CustomUser.objects.all()
        data_source = user.filter(sub_fun__user=self.request.user)
        sub_serializer = SubscrimeSerializer(
            self.paginate_queryset(data_source),
            context={'request': request},
            many=True,
        )

        if not data_source.exists():
            return Response(
                {'Вы не подписались ни на кого'},
                status=status.HTTP_400_BAD_REQUEST
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
    def get_generate_shopcart_file(self, request):
        ingredients = IngredientsRecipe.objects.filter(
            recipe__shoppingcart__user=self.request.user
        )
        uniq_ingredients = defaultdict(lambda: {'amount': 0, 'unit': ''})
        dict_value = ingredients.values(
            'ingredient__name',
            'ingredient__measurement_unit',
        )
        amount = dict_value.annotate(amount=Sum('amount'))
        for i in amount:
            name = i['ingredient__name']
            amount = i['amount']
            measurement_unit = i['ingredient__measurement_unit']
            uniq_ingredients[name]['amount'] += amount
            uniq_ingredients[name]['unit'] = measurement_unit

        shopcart_file_content = '\n'.join(
            [
                f'{name} - {data["amount"]} {data["unit"]}'
                for name, data in uniq_ingredients.items()
            ]
        )
        return self._create_download_response(
            shopcart_file_content,
            filename='shopping-list.txt'
        )

    def _create_download_response(self, content, filename):
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
