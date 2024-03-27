# Generated by Django 4.2.9 on 2024-03-18 08:32

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_alter_customuser_first_name_and_more'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='subscrime',
            name='unique_subscriber',
        ),
        migrations.AlterField(
            model_name='customuser',
            name='username',
            field=models.CharField(max_length=150, unique=True, validators=[django.core.validators.RegexValidator(message='Некорректно', regex='^[\\w.@+-]+$')], verbose_name='НИК пользователя'),
        ),
        migrations.AddConstraint(
            model_name='subscrime',
            constraint=models.UniqueConstraint(fields=('user', 'author'), name='unique_subscribers'),
        ),
    ]