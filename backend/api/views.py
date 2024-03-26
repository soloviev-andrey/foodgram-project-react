from django.shortcuts import get_object_or_404
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
    FavoriteSerializer,
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    RecipeCutSerializer,
    RecipeSerializer,
    ShoppingCartSerializer,
    SubscrimeSerializer,
    TagSerializer
)
User = get_user_model()

class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(
            detail=False,
            url_path='subscriptions',
            url_name='subscriptions',
            permission_classes=[IsAuthenticated,],
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(
            follower__user=request.user
        )
        if queryset.exists():
            serializer = SubscrimeSerializer(
                self.paginate_queryset(queryset),
                context={'request': request},
                many=True
            )
            return self.get_paginated_response(serializer.data)
        return Response(
            'Вы ни на кого не подписаны.',
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=True,
        methods=['POST'],
        url_path='subscribe',
        url_name='subscribe',
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(User, id=id)
        if user == author:
            return Response(
                'На себя подписываться нельзя!',
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription, created = Subscrime.objects.get_or_create(
            user=user,
            author=author
        )
        if not created:
            return Response(
                f'Вы уже подписаны на {author}',
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            f'Вы подписались на {author}',
            status=status.HTTP_201_CREATED
        )

    @subscribe.mapping.delete
    def unsubscribe(self, request, id):
        user = request.user
        author = get_object_or_404(User, id=id)

        change_subscription = Subscrime.objects.filter(
            user=user,
            author=author
        )
        if change_subscription.exists():
            change_subscription.delete()
            return Response(
                f'Вы больше не подписаны на {author}',
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            f'Вы не были подписаны на {author}',
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
            'recipe_ingredients__ingredient',
            'tags',
            'author'
        ).all()

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeCreateUpdateSerializer

    def _create_or_destroy(self, request, model, serializer):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=self.kwargs.get('pk'))
        if not recipe:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
        instance, created = model.objects.get_or_create(
            user=user,
            recipe=recipe
        )
        if request.method == 'POST':
            serializer = serializer(instance, context={'request': request})
            return {
                'data': serializer.data,
                'status': status.HTTP_201_CREATED
            }
        elif request.method == 'DELETE':
            instance.delete()
            return {'status': status.HTTP_204_NO_CONTENT}

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, **kwargs):
        return self._create_or_destroy(request, Favorite, FavoriteSerializer)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        url_path='shopping_cart',
        url_name='shopping_cart',
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, **kwargs):
        return self._create_or_destroy(request, ShoppingCart, ShoppingCartSerializer)