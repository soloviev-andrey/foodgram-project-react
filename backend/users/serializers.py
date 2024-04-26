from django.contrib.auth.models import AnonymousUser
from djoser.serializers import UserCreateSerializer, UserSerializer
from recipes.constant import User
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

from users.models import Subscrime


class ExtendedUserSerializer(UserSerializer):
    '''Сериализатор отображения пользователя'''
    is_subscribed = serializers.SerializerMethodField()

    def to_representation(self, instance):
        if isinstance(instance, AnonymousUser):
            raise AuthenticationFailed(
                'Неавторизованный пользователь'
            )
        return super().to_representation(instance)

    def get_is_subscribed(serializer, target):
        request = serializer.context.get('request')
        if request and request.user.is_staff:
            try:
                obj = Subscrime.objects.get(  # noqa
                    author=target
                )
                return True
            except Subscrime.DoesNotExist:
                return False
            except Exception as e:
                print(f'Что-то пошло не так: {e}')

        return False

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
