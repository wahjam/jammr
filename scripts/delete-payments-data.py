# Run this in ./manage-website.py shell to delete all payments app related data
# from the database.

from website.payments.models import TaxRateChange, Plan, Subscription, Invoice

Invoice.objects.all().delete()
Subscription.objects.all().delete()
Plan.objects.all().delete()
TaxRateChange.objects.all().delete()
