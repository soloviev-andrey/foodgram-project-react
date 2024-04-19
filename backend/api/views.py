from rest_framework.filters import SearchFilter
from io import StringIO
from django.contrib.auth import get_user_model
from django.db.models import Sum
import csv
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (Favorite, Ingredient, IngredientsRecipe, Recipe,
                            ShoppingCart, Tag)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from users.models import Subscrime

from api.filters import RecipeFilter
from api.permissions import IsAuthorOrReadOnly
from users.serializers import ExtendedUserSerializer
from api.serializers import (IngredientSerializer, SnippetRecipeSerializer,
                          RecipeCreateUpdateSerializer,
                          RecipeSerializer, SubscrimeSerializer, TagSerializer)


CustomUser = get_user_model()

class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = [SearchFilter,]
    
    def get_queryset(self):
        queryset = self.queryset
        name = self.request.query_params.get('name', None)
        search_method = self.request.query_params.get('search_method', 'startswith')
    
        if name is not None:
            if search_method == 'contains':
                queryset = queryset.filter(name__icontains=name)
            elif search_method == 'endswith':
                queryset = queryset.filter(name__iendswith=name)
            else:
                # По умолчанию используем istartswith
                queryset = queryset.filter(name__istartswith=name)
        return queryset

class CustomUserViewSet(UserViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = ExtendedUserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly,]

    @action(
        detail=True,
        methods=['POST','DELETE',],
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
        data_source = CustomUser.objects.filter(author__user=self.request.user)
        sub_serializer = SubscrimeSerializer(
                self.paginate_queryset(data_source),
                context={'request': request},
                many=True
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
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method != 'GET':
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def create_or_destroy(self, request, model, serializer):

        if request.method == 'POST':
            try:
                recipe_id = self.kwargs.get('pk')
                recipe_obj = Recipe.objects.get(pk=recipe_id)
            except Recipe.DoesNotExist:
                return Response(
                    'Рецепт не найден',
                    status.HTTP_400_BAD_REQUEST
                )
            obj, added = model.objects.select_related(
                'user',
                'recipe',
            ).get_or_create(user=request.user, recipe=recipe_obj)

            if added:
                serializer = SnippetRecipeSerializer(
                    recipe_obj,
                    context={'request': request}
                )
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                'Вы уже совершили это действие!',
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'DELETE':
            try:
                recipe_id = self.kwargs.get('pk')
                recipe_obj = Recipe.objects.get(pk=recipe_id)
            except Recipe.DoesNotExist:
                return Response(
                    'Рецепт не найден',
                    status=status.HTTP_404_NOT_FOUND
                )
            obj, added = model.objects.select_related(
                'user',
                'recipe',
            ).get_or_create(user=request.user, recipe=recipe_obj)
            if not added:
                obj.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                'Нечего удалять',
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, **kwargs):
        return self.create_or_destroy(
            request,
            ShoppingCart,
            self.kwargs.get('pk')
        )

    @action(
        detail=False,
        methods=['GET'],
        url_path='download_shopping_cart',
        permission_classes=(IsAuthenticated,),
    )
    def get_shopcart_file(self, request):
        format = request.query_params.get('format', 'txt')
        ingredients = IngredientsRecipe.objects.filter(
            recipe__shoppingcart__user=self.request.user
            )

        dict_value = ingredients.values(
                'ingredient__name',
                'ingredient__measurement_unit',
                ).annotate(amount=Sum('amount'))
        
        if format == 'txt':
            shopcart_file = []
            for ing in dict_value:
                shopcart_file.append(
                    '{name} - {amount} {measurement_unit}\n'.format(
                        name=ing.get('ingredient__name'),
                        amount=ing.get('amount'),
                        measurement_unit=ing.get(
                            'ingredient__measurement_unit'
                        )
                    )
                )
            response = HttpResponse(shopcart_file, content_type='text/plain')
            response['Content-Disposition'] = (
                'attachment; filename=shopping-list.txt'
            )
        elif format == 'csv':
            csv_data = StringIO()
            csv_writer = csv.writer(csv_data)
            csv_writer.writerow(
                [
                    'Наименование',
                    'Кол-во',
                    'Единица измерения товара'
                ]
            )
            for ingredient in ingredients:
                csv_writer.writerow([
                    ingredient.get('ingredient__name'),
                    ingredient.get('amount'),
                    ingredient.get('ingredient__measurement_unit')
                ])
            response = HttpResponse(csv_data.getvalue(), content_type='text/csv')
            response['Content-Disposition'] = (
                'attachment; filename=shopping-list.csv'
        )
        else:
            return HttpResponse("Unsupported format", status=400)

        return response


        

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, **kwargs): 
        return self.create_or_destroy(
            request,
            Favorite,
            self.kwargs.get('pk')
        )
