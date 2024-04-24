import base64

from django.core.files.base import ContentFile
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
                    raise serializers.ValidationError('Недопустимый формат файла')
                
                if self.max_size is not None and len(imgstr) > self.max_size:
                    raise serializers.ValidationError('Файл слишком большой')

                data = ContentFile(
                    base64.b64decode(imgstr),
                    name='temp.' + ext
                )
        except(
            TypeError,
            ValueError,
            AttributeError,
            UnicodeDecodeError,
        ) as e:
            raise serializers.ValidationError('Неподдерживаемый формат фото или рисунка')
        
        return super().to_internal_value(data)