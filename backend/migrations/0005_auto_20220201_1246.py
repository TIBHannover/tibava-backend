# Generated by Django 3.1.1 on 2022-02-01 12:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0004_auto_20220131_2127'),
    ]

    operations = [
        migrations.AlterField(
            model_name='videoanalyse',
            name='results',
            field=models.BinaryField(null=True),
        ),
    ]
