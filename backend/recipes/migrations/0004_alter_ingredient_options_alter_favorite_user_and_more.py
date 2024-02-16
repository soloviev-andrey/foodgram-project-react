# Generated by Django 4.2.9 on 2024-02-16 06:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        ('recipes', '0003_shoppingcart_favorite'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ingredient',
            options={'verbose_name': 'Ингредиент', 'verbose_name_plural': 'Ингредиент'},
        ),
        migrations.AlterField(
            model_name='favorite',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorite', to='users.customuser', verbose_name='Пользователь'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipes', to='users.customuser', verbose_name='Автор публикации (пользователь)'),
        ),
        migrations.AlterField(
            model_name='shoppingcart',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shopping_cart', to='users.customuser'),
        ),
    ]
