# Generated by Django 3.1.1 on 2022-04-19 08:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0008_auto_20220419_0854'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shortcut',
            name='keys',
            field=models.JSONField(null=True),
        ),
    ]