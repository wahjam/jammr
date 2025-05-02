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
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('subscription', models.SmallIntegerField(default=0, choices=[(0, 'Free'), (1, 'Full')])),
                ('instruments', models.TextField(max_length=80, blank=True)),
                ('influences', models.TextField(max_length=256, blank=True)),
                ('last_ip', models.GenericIPAddressField()),
                ('email_recorded_jams', models.BooleanField(default=True)),
                ('mail_optin', models.BooleanField(default=False)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
