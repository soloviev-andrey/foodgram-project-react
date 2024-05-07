import base64

from api.decorators import customrecipefields_decorator, get_field_decorator
from django.core.files.base import ContentFile
from recipes.models import Favorite, ShoppingCart
from rest_framework import serializers


class ExtendedImageField(serializers.ImageField):
    def __init__(self, *args, **kwargs):
        self.valid_formats = kwargs.pop(
            'valid_formats',
            ['jpg', 'jpeg', 'png', 'gif']
        )
        self.max_size = kwargs.pop('max_size', None)
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        try:
            if isinstance(data, str) and data.startswith('data:image'):
                format, imgstr = data.split(';base64,')
                ext = format.split('/')[-1]
                if ext not in self.valid_formats:
                    raise serializers.ValidationError(
                        'Недопустимый формат файла'
                    )

                if self.max_size is not None and len(imgstr) > self.max_size:
                    raise serializers.ValidationError(
                        'Файл слишком большой'
                    )
                data = ContentFile(
                    base64.b64decode(imgstr),
                    name='temp.' + ext
                )
        except (
            TypeError
        ):
            raise serializers.ValidationError(
                'Неподдерживаемый формат фото или рисунка'
            )

        return super().to_internal_value(data)


class RecipeIngredientsExtendedSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    measurement_unit = serializers.SerializerMethodField()
    amount = serializers.IntegerField()
    get_id = get_field_decorator('id')
    get_name = get_field_decorator('name')
    get_measurement_unit = get_field_decorator('measurement_unit')


class CustomRecipeFieldsSerializer(serializers.Serializer):
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    @customrecipefields_decorator(Favorite)
    def get_is_favorited(self, instance):
        pass

    @customrecipefields_decorator(ShoppingCart)
    def get_is_in_shopping_cart(self, instance):
        pass


class BaseFielsSerializer(serializers.ModelSerializer):
    '''Базовый класс для сериализаторов тэгов и ингредиентов'''
    class Meta:
        abstract = True
        fields = '__all__'
