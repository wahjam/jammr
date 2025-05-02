# Copyright 2019 Stefan Hajnoczi <stefanha@gmail.com>

import datetime
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from website.recorded_jams.models import RecordedJam

class Command(BaseCommand):
    help = 'Print recorded jam statistics'

    def handle(self, *args, **options):
        now = timezone.now()
        start_date = now - datetime.timedelta(days=365)
        bucket_end_date = start_date
        buckets = []

        for jam in RecordedJam.objects.filter(start_date__gte=start_date,
                                              duration__gt=datetime.time(minute=5)).order_by('start_date'):
            while jam.start_date >= bucket_end_date:
                buckets.append(set())
                bucket_end_date += datetime.timedelta(days=30)

            buckets[-1].update(set(u.username for u in jam.users.all()))

        self.stdout.write('Month\tCount\tUsernames\n')
        i = 0
        while i < 12 and i < len(buckets):
            self.stdout.write('%d\t%d\t%s\n' % (i - 12, len(buckets[i]), ', '.join(buckets[i])))
            i += 1
