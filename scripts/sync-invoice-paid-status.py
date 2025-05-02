# Run this in ./manage-website.py shell to synchronize Invoice objects in the
# website database with Stripe.  Invoice emails will be sent to customers if a
# payment succeeded.
import stripe
from website.payments.models import Invoice
invoices = Invoice.objects.filter(paid=False)
for i in invoices:
    si = stripe.Invoice.retrieve(i.stripe_invoice_id)
    i = Invoice.get_or_create(si)
    if si.paid:
        print('invoice {} has been paid'.format(si.id))
        i.pay()
