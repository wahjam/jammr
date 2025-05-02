# Copyright 2014-2019 Stefan Hajnoczi <stefanha@gmail.com>

from django.core.management.base import BaseCommand, CommandError
from website.jammr import models

class Command(BaseCommand):
    help = 'Find suspicious user accounts'

    def handle(self, *args, **options):
        same_ip = {}
        for profile in models.UserProfile.objects.all():
            count = same_ip.get(profile.last_ip, 1)
            count += 1
            same_ip[profile.last_ip] = count
        same_ip = sorted(((ip, count) for ip, count in same_ip.items() if count > 1),
                         key=lambda pair: pair[1], reverse=True)

        for ip, count in same_ip:
            self.stdout.write('%s %d\n' % (ip, count))
