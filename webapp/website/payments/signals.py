# Copyright (C) 2015-2024 Stefan Hajnoczi <stefanha@gmail.com>

import django.dispatch


# Sent when subscription is successful.  The sender argument is a
# models.Subscription instance.  The is_trialing argument is True if the
# subscript starts with a trial period and False otherwise.
user_subscribed = django.dispatch.Signal(providing_args=['is_trialing'])

# Sent when a subscription ends.  The sender argument is a models.Subscription
# instance.
user_unsubscribed = django.dispatch.Signal(providing_args=[])

# Sent when subscription renewal is canceled.  The sender argument is a
# models.Subscription instance.
renewal_canceled = django.dispatch.Signal(providing_args=[])

# Sent when invoice is paid.  The sender argument is a models.Invoice instance.
# The subscription argument is a models.Subscription instance.  The
# billing_details argument is a dictionary with 'email', 'name', and 'address'
# keys, where 'address' is a dict containing 'city', 'country', 'line1',
# 'line2', 'postal_code', and 'state' fields.
invoice_paid = django.dispatch.Signal(providing_args=['subscription', 'billing_details'])

# Sent when payment details are updated.  The sender argument is a
# models.Subscription instance.
payment_details_updated = django.dispatch.Signal(providing_args=[])
