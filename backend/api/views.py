from django.shortcuts import get_object_or_404
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
            methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,),
            pagination_class=None
    )
    def shopping_cart(self, request, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs['pk'])

        if request.method == 'POST':
            serializer = RecipeSerializer(recipe, data=request.data,
                                          context={"request": request})
            serializer.is_valid(raise_exception=True)
            if not ShoppingCart.objects.filter(user=request.user,
                                                recipe=recipe).exists():
                ShoppingCart.objects.create(user=request.user, recipe=recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response({'errors': 'Рецепт уже в списке покупок.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            try:
                shopping_cart_item = ShoppingCart.objects.get(user=request.user, recipe=recipe)
                shopping_cart_item.delete()
                return Response(
                    {'detail': 'Рецепт успешно удален из списка покупок.'},
                    status=status.HTTP_204_NO_CONTENT
                )
            except ShoppingCart.DoesNotExist:
                raise ValidationError('Рецепт не найден в списке покупок.', code='not_found')
    
        raise ValidationError('Недопустимый метод запроса.', code='invalid_method')
    
    @action(
        detail=False,
        methods=("get",),
        permission_classes=(IsAuthenticated,),
        url_path="download_shopping_cart",
        url_name="download_shopping_cart",
    )
    def download_shopping_cart(self, request):
        shopping_cart = ShoppingCart.objects.filter(user=self.request.user)
        recipes = Recipe.objects.filter(recipe_ingredients__recipe__in=shopping_cart)
        buy = (
            IngredientsRecipe.objects.filter(recipe__in=recipes)
            .values("ingredient")
            .annotate(amount=Sum("amount"))
        )

        purchased = [
            "Список покупок:",
        ]
        for item in buy:
            ingredient_id = item["ingredient"]
            try:
                ingredient = Ingredient.objects.get(pk=ingredient_id)
                amount = item["amount"]
                purchased.append(
                    f"{ingredient.name}: {amount}, {ingredient.unit_of_measurement}"
                )
            except Ingredient.DoesNotExist:
                purchased.append(f"Ингредиент с ID {ingredient_id} не найден")

        purchased_in_file = "\n".join(purchased)

        response = HttpResponse(purchased_in_file, content_type="text/plain")
        response["Content-Disposition"] = "attachment; filename=shopping-list.txt"

        return response