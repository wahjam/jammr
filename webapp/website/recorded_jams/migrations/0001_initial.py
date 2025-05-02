# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RecordedJam',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('start_date', models.DateTimeField()),
                ('mix_url', models.URLField()),
                ('tracks_url', models.URLField()),
                ('duration', models.TimeField()),
                ('server', models.CharField(max_length=128)),
                ('owner', models.ForeignKey(blank=True, null=True, related_name='owned_jams', to=settings.AUTH_USER_MODEL)),
                ('users', models.ManyToManyField(related_name='recorded_jams', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'permissions': (('can_download_tracks', 'Can download tracks'),),
            },
        ),
    ]
