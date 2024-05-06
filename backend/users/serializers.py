from djoser.serializers import UserCreateSerializer, UserSerializer
from api.decorators import subscribed_decorator, user_auth_decorator
from recipes.constant import User
from rest_framework import serializers


class ExtendedUserSerializer(UserSerializer):
    '''Сериализатор отображения пользователя'''
    is_subscribed = serializers.SerializerMethodField()

    @user_auth_decorator
    def to_representation(self, instance):
        return super().to_representation(instance)

    @subscribed_decorator
    def get_is_subscribed(self, target: User):
        pass

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed',
        )


class ExtendedAddUserSerializer(UserCreateSerializer):
    '''Сериализатор регистрации и создания пользователя'''
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
        )
