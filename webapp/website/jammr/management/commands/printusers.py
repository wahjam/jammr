# Copyright 2018-2020 Stefan Hajnoczi <stefanha@gmail.com>

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Print all usernames and email addresses'

    def handle(self, *args, **options):
        for u in User.objects.exclude(username='wahjamsrv').exclude(username='recorded_jams').order_by('-last_login'):
            self.stdout.write('%s %s\n' % (u.username, u.email))
