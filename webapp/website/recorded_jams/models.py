# Copyright 2013-2020 Stefan Hajnoczi <stefanha@gmail.com>

import datetime
from django.db import models
from django.core.mail import get_connection
from django.contrib.auth.context_processors import PermWrapper
from django.utils.timezone import utc
from website.utils import send_html_template_email

# Date when recorded jams became a premium-only feature
enforce_access_check_date = datetime.datetime(2020, 4, 16, tzinfo=utc)


class RecordedJam(models.Model):
    start_date = models.DateTimeField()
    owner = models.ForeignKey('auth.User', null=True, blank=True, related_name='owned_jams')
    users = models.ManyToManyField('auth.User', related_name='recorded_jams')
    mix_url = models.URLField()
    tracks_url = models.URLField()
    duration = models.TimeField()
    server = models.CharField(max_length=128)

    class Meta:
        permissions = (
            ('can_download_tracks', 'Can download tracks'),
            ('can_access_recorded_jams', 'Can access recorded jams'),
        )

    @models.permalink
    def get_absolute_url(self):
        return ('recorded_jam_view', (str(self.id),))

    def can_user_download_tracks(self, user):
        '''Is the user allowed to download individual tracks for this recorded jam?'''
        if self.start_date < enforce_access_check_date:
            return True
        return user.has_perm('recorded_jams.can_download_tracks')

    def can_user_access(self, user):
        '''Is the user allowed to access this recorded jam?'''
        # Private jams are only visible to users that participated
        if self.owner is not None:
            if not self.users.filter(id=user.id):
                return False

        if self.start_date < enforce_access_check_date:
            return True

        return user.has_perm('recorded_jams.can_access_recorded_jams')

    def email_users(self):
        '''Notify users by email'''
        connection = get_connection()
        for user in self.users.all():
            if not self.can_user_access(user):
                continue
            if not user.userprofile.email_recorded_jams:
                continue

            send_html_template_email(
                    [user.email],
                    'recorded_jams/email_users',
                    {
                        'user': user,
                        'perms': PermWrapper(user),
                        'jam': self,
                    },
                    connection=connection)
