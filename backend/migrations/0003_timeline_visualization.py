# Generated by Django 3.1.1 on 2022-06-01 09:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0002_auto_20220530_1159'),
    ]

    operations = [
        migrations.AddField(
            model_name='timeline',
            name='visualization',
            field=models.CharField(choices=[('C', 'COLOR'), ('CC', 'CATEGORYCOLOR'), ('SC', 'SCALARCOLOR'), ('SL', 'SCALARLINE')], default='C', max_length=2),
        ),
    ]