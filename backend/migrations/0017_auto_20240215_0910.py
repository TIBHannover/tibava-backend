# Generated by Django 3.1.1 on 2024-02-15 09:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("backend", "0016_auto_20240212_1359"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="clustertimelineitem",
            name="timeline",
        ),
        migrations.AlterField(
            model_name="clusteritem",
            name="plugin_run_result",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="cluster_items",
                to="backend.pluginrunresult",
            ),
        ),
    ]
