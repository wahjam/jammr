# Run this in ./manage-website.py shell to calculate VAT for the past 3 months.
import datetime
import decimal
import stripe
from django.utils import timezone
from website.payments.models import Invoice

today = datetime.datetime.today()
first = datetime.datetime(today.year, today.month, 1)
month_ranges = []

for i in range(3):
    old = first
    last = first - datetime.timedelta(1)
    first = datetime.datetime(last.year, last.month, 1)
    month_ranges.insert(0, (timezone.make_aware(first), timezone.make_aware(old)))

headers = ['Country']
for first, _ in month_ranges:
    month = first.strftime('%B').capitalize()
    headers.append(f'TaxPercentage{month}')
    headers.append(f'{month}EUR')
    headers.append(f'{month}GBP')
    headers.append(f'{month}USD')

print(','.join(headers))

for tax_rate in stripe.TaxRate.list(active=True, limit=100)['data']:
        country = tax_rate['jurisdiction']
        cells = []
        had_payments = False
        
        for this_month, next_month in month_ranges:
            invoices = Invoice.objects.filter(tax_country=country, paid=True, refunded=False, amount__gt=0, date__gte=this_month, date__lt=next_month)
            totals = {}
            for invoice in invoices:
                currency = invoice.currency
                t = totals.get(currency, decimal.Decimal(0))
                totals[currency] = t + invoice.amount / ((decimal.Decimal(100) + invoice.tax_percentage) / decimal.Decimal(100))
            cells.append(invoices[0].tax_percentage if invoices else decimal.Decimal(0))
            for currency in ('eur', 'gbp', 'usd'):
                if currency not in totals:
                    cells.append(decimal.Decimal(0))
                    continue
                if totals[currency] > decimal.Decimal(0):
                    had_payments = True
                cells.append(totals[currency].quantize(decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP))
        
        if had_payments:
            print('{},{}'.format(country, ','.join(str(c) for c in cells)))
