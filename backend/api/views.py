from djoser.views import UserViewSet
from .serializers import (
    CustomUserCreateSerializer,
    TagSerializer,
    IngredientSerializer,
)


from rest_framework import viewsets, generics
from recipes.models import Ingredient, Tag


class CustomUserCreateView(UserViewSet):
    serializer_class = CustomUserCreateSerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


