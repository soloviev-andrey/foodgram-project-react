# Generated by Django 4.2.9 on 2024-02-22 08:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_subscrime'),
    ]

    operations = [
        migrations.RenameField(
            model_name='subscrime',
            old_name='users',
            new_name='user',
        ),
    ]
