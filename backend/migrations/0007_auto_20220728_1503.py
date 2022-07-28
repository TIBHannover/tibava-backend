# Generated by Django 3.1.1 on 2022-07-28 15:03

import backend.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0006_auto_20220728_1453'),
    ]

    operations = [
        migrations.AlterField(
            model_name='annotation',
            name='color',
            field=models.CharField(default=backend.models.random_color_string, max_length=256),
        ),
        migrations.AlterField(
            model_name='annotationcategory',
            name='color',
            field=models.CharField(default=backend.models.random_color_string, max_length=256),
        ),
    ]
