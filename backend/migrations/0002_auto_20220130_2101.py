# Generated by Django 3.1.1 on 2022-01-30 21:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='duration',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='video',
            name='fps',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='video',
            name='height',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='video',
            name='width',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
