# Generated by Django 3.1.1 on 2024-05-07 08:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0021_videoanalysisstate'),
    ]

    operations = [
        migrations.AddField(
            model_name='videoanalysisstate',
            name='selected_face_clustering',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='video_analyses_state_face_clustering', to='backend.pluginrun'),
        ),
        migrations.AddField(
            model_name='videoanalysisstate',
            name='selected_place_clustering',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='video_analyses_state_place_clustering', to='backend.pluginrun'),
        ),
    ]
