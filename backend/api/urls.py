# from .views import UserViewSet
from django.urls import include, path, re_path
from rest_framework import routers

from api.views import IngredientViewSet, TagViewSet, CustomUserViewSet

app_name = 'api'
router = routers.DefaultRouter()
router.register('users', CustomUserViewSet, basename='users')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('tags', TagViewSet, basename='tags')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]

