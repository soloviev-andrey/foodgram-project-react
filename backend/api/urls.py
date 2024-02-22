from django.urls import include, path
from rest_framework.routers import DefaultRouter
from api.views import CustomUserCreateView, TagViewSet

app_name = 'api'
router = DefaultRouter()
router.register('users', CustomUserCreateView, basename='users')
router.register('tags', TagViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
