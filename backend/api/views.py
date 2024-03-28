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
        author_id = kwargs.get('id')
        author = get_object_or_404(User, id=author_id)
        
        if author == request.user:
            return Response(
                {'error': 'На себя подписываться нельзя!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription, created = Subscrime.objects.get_or_create(
            user=request.user, author=author
        )
        
        if request.method == 'POST':
            if not created:
                return Response(
                    {'error': f'Вы уже подписаны на {author}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = SubscrimeSerializer(
                author,
                context={'request': request}
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        
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
        serializer = SubscrimeSerializer(
            self.paginate_queryset(queryset),
            context={'request': request},
            many=True
        )
        return self.get_paginated_response(serializer.data)

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

    def create_or_destroy(self, request, model, id):
        recipe = get_object_or_404(Recipe, id=id)
        if not recipe:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
        instance, created = model.objects.select_related(
            'user', 'recipe'
        ).get_or_create(user=request.user, recipe=recipe)
        if request.method == 'POST' and created:
            serializer = RecipeCutSerializer(
                recipe,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE' and instance:
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        raise ValidationError(
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
        return self.create_or_destroy(
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
        recipe_id = self.kwargs.get('pk')
        try:
            recipe = Recipe.objects.get(pk=recipe_id)
        except Recipe.DoesNotExist:
            return Response(
                {'Рецепт не существует'},
                status.HTTP_400_BAD_REQUEST
            )

        try:
            shopping_cart_item, created = ShoppingCart.objects.get_or_create(
                user=request.user,
                recipe=recipe
            )
        
            if request.method == 'POST':
                if not created:
                    return Response(
                        {'Рецепт уже в корзине покупок'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                serializer = RecipeCutSerializer(
                    recipe,
                    context={'request': request}
                )
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
        
            shopping_cart_item.delete()
            return Response(
                {'Рецепт удален из корзины покупок'},
                status=status.HTTP_204_NO_CONTENT
            )
        except IntegrityError:
            return Response(
                {'Рецепт уже в корзине покупок'},
                status=status.HTTP_400_BAD_REQUEST
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

