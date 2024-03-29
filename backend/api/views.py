from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from django.db.models import Sum
from django.http import HttpResponse
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientsRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    SAFE_METHODS,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)

from rest_framework.response import Response
from users.models import Subscrime
from django.contrib.auth import get_user_model

from api.filters import IngredientNameFilter, RecipeFilter
from api.permissions import IsAuthorOrReadOnly

from .serializers import (
    CustomUserSerializer,
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    RecipeCutSerializer,
    RecipeSerializer,
    SubscrimeSerializer,
    TagSerializer
)
User = get_user_model()
class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        url_path='subscribe',
        url_name='subscribe',
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, **kwargs):
        author = get_object_or_404(User, id=self.kwargs.get('id'))
        if author == request.user:
            raise ValidationError(
                detail='Нельзя подписаться на самого себя.',
                code=400
            )
        subscription, created = Subscrime.objects.get_or_create(
            user=request.user, author=author
        )
        if request.method == 'POST':
            if not created:
                raise ValidationError(
                    detail='Вы уже подписаны на данного автора.',
                    code=400
                )
            serializer = SubscrimeSerializer(author, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)   
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

        



        


    @action(
        detail=False,
        methods=['GET'],
        url_path='subscriptions',
        url_name='subscriptions',
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(author__user=self.request.user)
        if queryset:
            serializer = SubscrimeSerializer(
                self.paginate_queryset(queryset),
                context={'request': request},
                many=True
            )
            return self.get_paginated_response(serializer.data)
        return Response(
            {'Вы не подписались ни на кого'},
             status=status.HTTP_400_BAD_REQUEST
        )

class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None

class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientNameFilter
    pagination_class = None

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (
        IsAuthenticatedOrReadOnly,
        IsAuthorOrReadOnly,
    )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        return Recipe.objects.prefetch_related(
            'ingredients_recipe__ingredient',
            'tags',
            'author',
        ).all()

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeCreateUpdateSerializer

    def create_or_destroy(self, request, model, serializer):
        recipe_id = self.kwargs.get('pk')
        try:
            recipe = Recipe.objects.get(pk=recipe_id)
        except Recipe.DoesNotExist:
            return Response(
                {'Рецепт не найден'},
                status.HTTP_400_BAD_REQUEST
            )
        instance, created = model.objects.select_related(
            'user',
            'recipe',
            ).get_or_create(user=request.user, recipe=recipe)
        if request.method == 'POST':
            if created:
                serializer = RecipeCutSerializer(
                    recipe,
                    context={'request': request}
                )
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {'Вы уже совершили это действие!'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
        if request.method == 'DELETE':
            if instance:
                instance.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'Нечего удалять'},
                status=status.HTTP_400_BAD_REQUEST
            ) 


    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        url_path='shopping_cart',
        url_name='shopping_cart',
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
        url_name='download_shopping_cart',
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        ingredients = (IngredientsRecipe.objects.filter(
            recipe__shopping_carts__user=request.user).values(
            'ingredient__name',
            'ingredient__measurement_unit',
        ).annotate(amount=Sum('amount')))
        purchased_in_file = []
        for ingredient in ingredients:
            purchased_in_file.append('{name} - {amount} {m_unit}\n'.format(
                name=ingredient.get('ingredient__name'),
                amount=ingredient.get('amount'),
                m_unit=ingredient.get('ingredient__measurement_unit')
            ))
        response = HttpResponse(purchased_in_file, content_type="text/plain")
        response["Content-Disposition"] = "attachment; filename=shopping-list.txt"

        return response


    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        url_path='favorite',
        url_name='favorite',
        permission_classes=(IsAuthenticated,),
    )
    def Favorite(self, request, **kwargs):
        return self.create_or_destroy(
            request,
            Favorite,
            self.kwargs.get('pk')
        )