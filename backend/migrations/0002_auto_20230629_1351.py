# Generated by Django 3.1.1 on 2023-06-29 13:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tibavauser',
            name='max_video_size',
            field=models.BigIntegerField(default=52428800),
        ),
    ]