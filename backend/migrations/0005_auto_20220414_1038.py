# Generated by Django 3.1.1 on 2022-04-14 10:38

import backend.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0004_auto_20220312_2042'),
    ]

    operations = [
        migrations.AddField(
            model_name='timeline',
            name='collapse',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='timeline',
            name='order',
            field=models.IntegerField(default=0),
        ),
        migrations.CreateModel(
            name='TimelineAnalyse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hash_id', models.CharField(default=backend.models.gen_hash_id, max_length=256)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('timeline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.timeline')),
                ('video_analyse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.videoanalyse')),
            ],
        ),
    ]
