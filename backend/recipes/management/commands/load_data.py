import csv
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Необходимо указать точную дерикторию к ФАЙЛУ CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Необходимо указать точную дерикторию к ФАЙЛУ CSV'
        )

    def handle(self, *args, **options):
        file_path = "C:/Dev/foodgram-project-react/data/ingredients.csv"
        with open(file_path, encoding='UTF-8') as file:
            for row in csv.reader(file):
                name, measurement_unit = row
                Ingredient.objects.create(
                    name=name,
                    measurement_unit=measurement_unit
                )
            self.stdout.write('Импорт данных завершен!')
