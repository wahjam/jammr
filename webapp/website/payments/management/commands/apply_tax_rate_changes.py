# Copyright 2020 Stefan Hajnoczi <stefanha@gmail.com>

from django.core.management.base import BaseCommand
from website.payments.models import TaxRateChange

class Command(BaseCommand):
    help = 'Apply pending tax rate changes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Print actions without making modifications'
        )

    def handle(self, *args, **options):
        TaxRateChange.apply_all(dry_run=options['dry_run'])
