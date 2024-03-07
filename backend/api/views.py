from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from api.pagination import LimitPageNumberPagination
from recipes.models import (Favorite, Ingredient, IngredientsRecipe, Recipe,
                            ShoppingCart, Tag)
from rest_framework import exceptions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (SAFE_METHODS, IsAuthenticated, IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from users.models import CustomUser, Subscrime

from api.filters import IngredientSearchFilter, RecipeFilter
from api.permissions import IsAuthorOrReadOnly

from .serializers import (CustomUserSerializer, IngredientSerializer,
                          RecipeCreateUpdateSerializer, RecipeCutSerializer,
                          RecipeSerializer, SubscrimeSerializer, TagSerializer)


class CustomUserViewSet(UserViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)

    @action(
        detail=False,
        methods=("get",),
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        """Список авторов, на которых подписан пользователь."""
        user = self.request.user
        queryset = user.subscribe.all()
        pages = self.paginate_queryset(queryset)
        serializer = SubscrimeSerializer(
            pages, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=("post", "delete"),
    )
    def subscribe(self, request, id=None):
        """Подписка на автора."""
        user = self.request.user
        author = get_object_or_404(CustomUser, pk=id)

        if user == author:
            return Response(
                {"errors": "Нельзя подписаться или отписаться от себя!"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if self.request.method == "POST":
            if Subscrime.objects.filter(user=user, author=author).exists():
                return Response(
                    {"errors": "Подписка уже оформлена!"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            queryset = Subscrime.objects.create(author=author, user=user)
            serializer = SubscrimeSerializer(
                queryset, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if self.request.method == "DELETE":
            if not Subscrime.objects.filter(
                user=user, author=author
            ).exists():
                return Response(
                    {"errors": "Вы уже отписаны!"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            subscription = get_object_or_404(
                Subscrime, user=user, author=author
            )
            subscription.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = None


class IngredienViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    filter_backends = IngredientSearchFilter
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        return Recipe.objects.prefetch_related(
            'recipe_ingredients__ingredient',
            'tags',
            'author'
        ).all()

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeCreateUpdateSerializer

    def add_remove_recipe(self, request, id, model):
        recipe = get_object_or_404(Recipe, id=id)
        obj, created = model.objects.select_related(
            'user', 'recipe'
        ).get_or_create(user=request.user, recipe=recipe)
        if request.method == 'POST' and created:
            serializer = RecipeCutSerializer(
                recipe,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE' and obj:
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        raise exceptions.ValidationError(
            detail='Вы уже совершили это действие!'
        )

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        url_path='favorite',
        url_name='favorite',
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, **kwargs):
        return self.add_remove_recipe(
            request,
            self.kwargs.get('pk'),
            Favorite
        )

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        url_path='shopping_cart',
        url_name='shopping_cart',
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, **kwargs):
        return self.add_remove_recipe(
            request,
            self.kwargs.get('pk'),
            ShoppingCart
        )

    @action(
        detail=False,
        methods=['GET'],
        url_path='download_shopping_cart',
        url_name='download_shopping_cart',
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        ingredients = (IngredientsRecipe.objects.filter(
            recipe__shopping_carts__user=request.user).values(
            'ingredient__name',
            'ingredient__measurement_unit',
        ).annotate(amount=Sum('amount')))
        pretty_ings = []
        for ingredient in ingredients:
            pretty_ings.append('{name} - {amount} {m_unit}\n'.format(
                name=ingredient.get('ingredient__name'),
                amount=ingredient.get('amount'),
                m_unit=ingredient.get('ingredient__measurement_unit')
            ))
        response = FileResponse(pretty_ings, content_type='text/plain')
        return response
