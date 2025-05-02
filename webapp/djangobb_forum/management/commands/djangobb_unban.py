from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from djangobb_forum.models import Ban


class Command(BaseCommand):
    help = 'Unban users'

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help='Unban all users')
        parser.add_argument('--by-time', action='store_true', help='Unban users by time')

    def handle(self, *args, **options):
        if options['all']:
            bans = Ban.objects.all()
            user_ids = bans.values_list('user', flat=True)
            User.objects.filter(id__in=user_ids).update(is_active=True)
            bans.delete()
        elif options['by_time']:
            bans = Ban.objects.filter(ban_end__lte=datetime.now())
            user_ids = bans.values_list('user', flat=True)
            User.objects.filter(id__in=user_ids).update(is_active=True)
            bans.delete()
        else:
            raise CommandError('Invalid options')
