import csv
from django.core.management.base import BaseCommand
from recipes.models import Ingredient

class Command(BaseCommand):
    help = 'Импорт ингредиентов из CSV файла'
    file_path = 'C:/Dev/foodgram-project-react/data/ingredients.csv'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Путь к файлу CSV с ингредиентами'
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        try:
            with open(file_path, encoding='UTF-8') as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    name, measurement_unit = row
                    Ingredient.objects.create(
                        name=name,
                        measurement_unit=measurement_unit
                    )
                self.stdout.write(self.style.SUCCESS('Импорт данных завершен!'))
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR('Файл не найден. Проверьте путь к файлу.'))
        except csv.Error:
            self.stderr.write(self.style.ERROR('Ошибка при чтении файла CSV. Проверьте формат файла.'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Произошла ошибка: {e}'))
