# Generated by Django 3.1.1 on 2023-08-09 17:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0007_face'),
    ]

    operations = [
        migrations.AddField(
            model_name='face',
            name='image_path',
            field=models.CharField(max_length=128, null=True),
        ),
    ]
