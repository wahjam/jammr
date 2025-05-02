# Run this in ./manage-website.py shell to add a coupon to all existing Premium
# subscriptions.  Set the COUPON_CODE variable to the Stripe Coupon id before
# running.
import stripe
from website.payments.models import Subscription
for s in Subscription.objects.filter(active=True, canceled=False):
    stripe.Subscription.modify(s.stripe_subscription_id,
            coupon=COUPON_CODE,
            metadata={'user_id': s.user.id})
