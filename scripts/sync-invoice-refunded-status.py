# Run this in ./manage-website.py shell to synchronize Invoice objects in the
# website database with Stripe.
import stripe
from website.payments.models import Invoice
invoices = Invoice.objects.filter(refunded=False)
for i in invoices:
    si = stripe.Invoice.retrieve(i.stripe_invoice_id)
    if not si.paid:
        continue
    if not si.charge:
        continue
    sc = stripe.Charge.retrieve(si.charge)
    if not sc.refunded:
        continue
    i = Invoice.get_or_create(si)
    if not i.refunded:
        print('invoice {} has been refunded'.format(si.id))
        i.refund()
