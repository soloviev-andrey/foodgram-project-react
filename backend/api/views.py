from djoser.views import UserViewSet
from rest_framework.response import Response

from api.permissions import IsAuthorOrReadOnly
from .serializers import (
    CustomUserSerializer,
    TagSerializer,
    IngredientSerializer,
    SubscrimeSerializer,
)
from api.pagination import LimitPageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework import viewsets, status
from recipes.models import Tag, Ingredient
from users.models import CustomUser, Subscrime
from django.shortcuts import get_object_or_404


class CustomUserViewSet(UserViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = LimitPageNumberPagination

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticated, ),
        url_path='subscribe',
        url_name='subscribe',
    )
    def subsribe(self, request, id=None):
        '''Подписка на автора'''
        user = self.request.user
        author = get_object_or_404(
            CustomUser,
            pk=id
        )
        if user == author:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
            )
        if self.request.method == 'POST':
            if Subscrime.objects.filter(
                user=user,
                author=author
            ).exists():
                return Response(
                    {'errors': 'Вы уже подписались на данного автора!'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            queryset = Subscrime.objects.create(
                author=author,
                user=user,
            )
            serializer = SubscrimeSerializer(
                queryset,
                context={'request': request},
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )

        if self.request.method == 'DELETE':
            if not Subscrime.objects.filter(
                user=user,
                author=author,
            ).exists():
                return Response(
                    {'errors': 'Вы уже оформлена отписка!'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            subscription = get_object_or_404(
                Subscrime,
                user=user,
                author=author,
            )
            subscription.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=False,
        methods=('GET',),
        permission_classes=(IsAuthenticated,),
        url_path='subscriptions',
        url_name='subscriptions',
    )
    def subscriptions(self, request):
        """Список авторов, на которых подписан пользователь."""
        user = self.request.user
        queryset = user.follower.all()
        pages = self.paginate_queryset(queryset)
        serializer = SubscrimeSerializer(
            pages,
            many=True,
            context={"request": request},
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = None


class IngredienViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
