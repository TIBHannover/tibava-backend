# Generated by Django 3.1.1 on 2023-08-10 09:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0008_face_image_path'),
    ]

    operations = [
        migrations.AddField(
            model_name='clustertimelineitem',
            name='plugin_run',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='backend.pluginrun'),
        ),
    ]