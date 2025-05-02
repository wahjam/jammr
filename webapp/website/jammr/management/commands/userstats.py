# Copyright 2013-2019 Stefan Hajnoczi <stefanha@gmail.com>

from django.core.management.base import BaseCommand, CommandError
from website.jammr import models

class Command(BaseCommand):
    help = 'Print user account statistics'

    def handle(self, *args, **options):
        results = []
        for value, name in models.SUBSCRIPTION_CHOICES:
            n = models.UserProfile.objects.filter(subscription__exact=value).count()
            results.append('%d %s' % (n, name))
        self.stdout.write(', '.join(results))
        self.stdout.write('\n')
