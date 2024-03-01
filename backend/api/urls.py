from django.urls import include, path
from rest_framework.routers import DefaultRouter
from api.views import (
    CustomUserViewSet,
    TagViewSet,
    IngredienViewSet,
)

app_name = 'api'
router = DefaultRouter()
router.register('users', CustomUserViewSet, basename='users')
router.register('tags', TagViewSet)
router.register('ingredients', IngredienViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('auth/', include('djoser.urls.jwt')),
]
