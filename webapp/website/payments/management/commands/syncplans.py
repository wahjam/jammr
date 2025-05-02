# Copyright 2015-2020 Stefan Hajnoczi <stefanha@gmail.com>

from django.core.management.base import BaseCommand
from website.payments.models import Plan


class Command(BaseCommand):
    help = 'Add new plans from Stripe into the database'

    def handle(self, *args, **options):
        new_plans, updated_plans = Plan.sync_plans()

        if not new_plans and not updated_plans:
            self.stdout.write('No changes to plans found in Stripe')
            return

        for plan in new_plans:
            self.stdout.write('Added "%s" plan, %g %s per month with Stripe Plan ID "%s"' % (
                plan.name,
                plan.amount,
                plan.currency,
                plan.stripe_plan_id))

        for plan in updated_plans:
            self.stdout.write('Updated "%s" plan, %g %s per month with Stripe Plan ID "%s"' % (
                plan.name,
                plan.amount,
                plan.currency,
                plan.stripe_plan_id))
