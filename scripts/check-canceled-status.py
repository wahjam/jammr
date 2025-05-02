# Run this in ./manage-website.py shell to check for Subscription objects that
# have canceled set to true but stripe.Subscription is not canceled.
import stripe
from website.payments.models import Subscription
subscriptions = Subscription.objects.filter(active=True, canceled=True)
for s in subscriptions:
    ss = stripe.Subscription.retrieve(s.stripe_subscription_id)
    if ss.status == 'canceled':
        continue
    if ss.cancel_at_period_end:
        continue
    print('{} stripe_subscription_id {}'.format(user.username, s.stripe_subscription_id))
