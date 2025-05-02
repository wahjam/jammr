# Copyright 2020 Stefan Hajnoczi <stefanha@gmail.com>

from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand, CommandError
from website.jammr.models import SUBSCRIPTION_FREE, UserProfile

class Command(BaseCommand):
    help = 'Add permissions to join private jams to free users'

    # This could be a data migration but it may take a long time to run, so use
    # a management command instead.
    def handle(self, *args, **options):
        can_join_private_jams = Permission.objects.get(codename='can_join_private_jams')

        total = UserProfile.objects.filter(subscription=SUBSCRIPTION_FREE).count()
        i = 0
        while i < total:
            for u in UserProfile.objects.filter(subscription=SUBSCRIPTION_FREE)[i:i + 1000]:
                user = u.user
                user.user_permissions.add(can_join_private_jams)
                user.save()

                i += 1
                if i % 500 == 0:
                    self.stdout.write('{}/{} users completed ({}%)'.format(i, total, 100 * i // total))
