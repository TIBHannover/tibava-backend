# Generated by Django 3.1.1 on 2022-08-10 16:12

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0009_auto_20220728_1532'),
    ]

    operations = [
        migrations.CreateModel(
            name='TimelineView',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=256)),
                ('timelines', models.ManyToManyField(to='backend.Timeline')),
                ('video', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.video')),
            ],
        ),
    ]
