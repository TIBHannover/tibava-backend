# Generated by Django 3.1.1 on 2023-08-02 05:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0004_clustertimelineitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='clustertimelineitem',
            name='video',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='backend.video'),
        ),
    ]
