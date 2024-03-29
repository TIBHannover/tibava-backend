# Generated by Django 3.1.1 on 2023-06-29 13:46

import backend.models
from django.conf import settings
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='TibavaUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('allowance', models.IntegerField(default=3)),
                ('max_video_size', models.IntegerField(default=52428800)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Annotation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=1024)),
                ('color', models.CharField(default=backend.models.random_color_string, max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='Plugin',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='PluginRun',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('update_date', models.DateTimeField(auto_now_add=True)),
                ('type', models.CharField(max_length=256)),
                ('progress', models.FloatField(default=0.0)),
                ('in_scheduler', models.BooleanField(default=False)),
                ('status', models.CharField(choices=[('U', 'UNKNOWN'), ('E', 'ERROR'), ('D', 'DONE'), ('R', 'RUNNING'), ('Q', 'QUEUED'), ('W', 'WAITING')], default='U', max_length=2)),
            ],
        ),
        migrations.CreateModel(
            name='PluginRunResult',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=256)),
                ('data_id', models.CharField(max_length=64, null=True)),
                ('type', models.CharField(choices=[('V', 'VIDEO'), ('I', 'IMAGES'), ('S', 'SCALAR'), ('H', 'HIST'), ('SH', 'SHOTS'), ('R', 'RGB_HIST')], default='S', max_length=2)),
                ('plugin_run', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.pluginrun')),
            ],
        ),
        migrations.CreateModel(
            name='Timeline',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=256)),
                ('type', models.CharField(choices=[('A', 'ANNOTATION'), ('R', 'PLUGIN_RESULT')], default='A', max_length=2)),
                ('order', models.IntegerField(default=-1)),
                ('collapse', models.BooleanField(default=False)),
                ('visualization', models.CharField(choices=[('C', 'COLOR'), ('CC', 'CATEGORY_COLOR'), ('SC', 'SCALAR_COLOR'), ('SL', 'SCALAR_LINE'), ('H', 'HIST')], default='C', max_length=2)),
                ('colormap', models.CharField(blank=True, max_length=256, null=True)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='backend.timeline')),
                ('plugin_run_result', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='backend.pluginrunresult')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='TimelineSegment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('color', models.CharField(max_length=256, null=True)),
                ('start', models.FloatField(default=0)),
                ('end', models.FloatField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=256)),
                ('license', models.CharField(max_length=256)),
                ('ext', models.CharField(max_length=256)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('fps', models.FloatField(blank=True, null=True)),
                ('duration', models.FloatField(blank=True, null=True)),
                ('height', models.IntegerField(blank=True, null=True)),
                ('width', models.IntegerField(blank=True, null=True)),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='TimelineSegmentAnnotation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('annotation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.annotation')),
                ('timeline_segment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.timelinesegment')),
            ],
        ),
        migrations.AddField(
            model_name='timelinesegment',
            name='annotations',
            field=models.ManyToManyField(through='backend.TimelineSegmentAnnotation', to='backend.Annotation'),
        ),
        migrations.AddField(
            model_name='timelinesegment',
            name='timeline',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.timeline'),
        ),
        migrations.AddField(
            model_name='timeline',
            name='video',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.video'),
        ),
        migrations.CreateModel(
            name='Shortcut',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('type', models.CharField(max_length=256, null=True)),
                ('keys', models.JSONField(null=True)),
                ('keys_string', models.CharField(max_length=256, null=True)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('video', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='backend.video')),
            ],
        ),
        migrations.AddField(
            model_name='pluginrun',
            name='video',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.video'),
        ),
        migrations.CreateModel(
            name='AnnotationShortcut',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('annotation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.annotation')),
                ('shortcut', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.shortcut')),
            ],
        ),
        migrations.CreateModel(
            name='AnnotationCategory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=256)),
                ('color', models.CharField(default=backend.models.random_color_string, max_length=256)),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('video', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='backend.video')),
            ],
        ),
        migrations.AddField(
            model_name='annotation',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='backend.annotationcategory'),
        ),
        migrations.AddField(
            model_name='annotation',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='annotation',
            name='video',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='backend.video'),
        ),
    ]
