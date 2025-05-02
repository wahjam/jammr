# Copyright (C) 2015-2024 Stefan Hajnoczi <stefanha@gmail.com>

import datetime
import decimal
import logging
import json
from django.contrib.gis.geoip import GeoIP
from django.contrib.sites.shortcuts import get_current_site
from django.db import models
from django.db.models import PROTECT
from django.db.utils import IntegrityError
from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import mail_admins
from django.urls import reverse
from django.utils.timezone import utc, make_aware, now
from . import signals
import stripe

logger = logging.getLogger('website.payments.models')
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')


def stripe_timestamp_to_datetime(timestamp):
    value = datetime.datetime.fromtimestamp(timestamp)
    return make_aware(value, timezone=utc)

def stripe_amount_to_decimal(amount):
    # Assumes currency is denoted in 1/100ths like USD, EUR, and GBP
    return decimal.Decimal('%d.%d' % (amount // 100, amount % 100))


def get_tax_rate_by_country_code(country):
    '''Return a stripe.TaxRate object for an ISO-3166-1 alpha-2 country code or None if no sales tax is necessary'''
    for tax_rate in stripe.TaxRate.list(active=True, limit=100)['data']:
        if tax_rate['jurisdiction'] == country:
            return tax_rate
    return None


class TaxRateChange(models.Model):
    '''Tax rate change'''
    country = models.CharField(max_length=2, help_text='ISO 3166-1 alpha-2 Country Code')
    percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text='Tax rate in percent')
    start_date = models.DateField(help_text='Date when new tax rate comes into effect')
    stripe_taxrate_id = models.CharField(max_length=255, help_text='Stripe TaxRate ID', blank=True)

    @staticmethod
    def apply_all(date=None, dry_run=True):
        '''Apply tax rate changes that have come into effect'''
        if date is None:
            today = now().date()
        for change in TaxRateChange.objects.filter(
                stripe_taxrate_id='',
                start_date__lte=today
            ).order_by('start_date'):
            change.apply(dry_run=dry_run)

    def apply(self, dry_run=True):
        old_tax_rate = get_tax_rate_by_country_code(self.country)
        if decimal.Decimal(old_tax_rate.percentage) == self.percentage:
            logger.warning('Cannot apply TaxRateChange {} for country {}. Already applied?'.format(
                self.id,
                self.country
            ))
            return

        if not dry_run:
            tax_rate = stripe.TaxRate.create(
                display_name='VAT',
                description='{} VAT'.format(self.country),
                jurisdiction=self.country,
                percentage=self.percentage,
                inclusive=True,
                metadata={'taxratechange_id': self.id}
            )

            stripe.TaxRate.modify(old_tax_rate.id, active=False)

            self.stripe_taxrate_id = tax_rate.id
            self.save()

            logger.info('Created TaxRate {} for country {} at {}%% and deactivated TaxRate {}'.format(
                tax_rate.id,
                self.country,
                self.percentage,
                old_tax_rate.id
            ))
        else:
            logger.info('Would create TaxRate for country {} at {}%% and deactivate TaxRate {}'.format(
                self.country,
                self.percentage,
                old_tax_rate.id
            ))

        for invoice in Invoice.objects.filter(tax_country=self.country, date__gte=self.start_date):
            logger.info('Updating tax rate on {} from {}%% to {}%%'.format(
                invoice,
                invoice.tax_percentage,
                self.percentage
            ))
            if not dry_run:
                invoice.tax_percentage = self.percentage
                invoice.save()


class Plan(models.Model):
    '''Subscription plan'''
    stripe_plan_id = models.CharField(max_length=255, help_text='Stripe Plan ID', unique=True)
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=3)
    visible = models.BooleanField()
    trial_period_days = models.PositiveIntegerField(default=0)

    @staticmethod
    def sync_plans():
        '''Synchronize plans from Stripe into our database'''
        new_plans = []
        updated_plans = []

        for stripe_plan in stripe.Plan.list().data:
            product = stripe.Product.retrieve(stripe_plan.product)
            amount = stripe_amount_to_decimal(stripe_plan.amount)

            plan, created = Plan.objects.get_or_create(
                    stripe_plan_id=stripe_plan.id,
                    defaults={
                        'name': product.name,
                        'amount': amount,
                        'currency': stripe_plan.currency,
                        'visible': stripe_plan.active,
                        'trial_period_days': stripe_plan.trial_period_days,
                    })

            if not created:
                need_save = plan.name != product.name or \
                            plan.amount != amount or \
                            plan.currency != stripe_plan.currency or \
                            plan.visible != stripe_plan.active or \
                            plan.trial_period_days != stripe_plan.trial_period_days

                plan.name = product.name
                plan.amount = amount
                plan.currency = stripe_plan.currency
                plan.visible = stripe_plan.active
                plan.trial_period_days = stripe_plan.trial_period_days

                if need_save:
                    plan.save()

            if created:
                new_plans.append(plan)
            elif need_save:
                updated_plans.append(plan)

        return new_plans, updated_plans

    @staticmethod
    def get_plan_by_country_code(country_code):
        '''Look up a suitable plan from an ISO 3166-1 alpha-2 country code'''
        euro_area = ('AT', 'BE', 'CY', 'DE', 'EE', 'ES', 'FI', 'FR', 'GR',
                     'IE', 'IT', 'LU', 'LV', 'MT', 'NL', 'PT', 'SI', 'SK')

        if country_code in euro_area:
            return Plan.objects.filter(visible=True, currency='eur')[0]
        elif country_code in ('UK', 'GB'):
            return Plan.objects.filter(visible=True, currency='gbp')[0]
        else:
            return Plan.objects.filter(visible=True, currency='usd')[0]

    def __str__(self):
        return 'Plan \"%s\" (%s) billed at %g %s' % (
                self.name,
                self.stripe_plan_id,
                self.amount,
                self.currency)


class Subscription(models.Model):
    '''Subscription of a User to a Plan'''
    user = models.ForeignKey(User, on_delete=PROTECT)
    plan = models.ForeignKey(Plan, on_delete=PROTECT)
    stripe_customer_id = models.CharField(max_length=255)
    stripe_subscription_id = models.CharField(max_length=255, help_text='Latest Stripe Subscription ID', unique=True)
    expires = models.DateField()

    # Is the subscription paid up or at least in the trial period?
    active = models.BooleanField(default=False, help_text='Currently valid')

    canceled = models.BooleanField(default=False, help_text='Finishes at end of billing period')
    ip_country = models.CharField(max_length=2) # ISO 3166-1 alpha-2 Country Code based on IP address
    billing_country = models.CharField(max_length=2, blank=True) # ISO 3166-1 alpha-2 Country Code based on billing address
    card_country = models.CharField(max_length=2, blank=True) # ISO 3166-1 alpha-2 Country Code based on credit card country

    @staticmethod
    def get_or_create(stripe_subscription):
        user_id = stripe_subscription.metadata.get('user_id')
        if user_id is None:
            # Old versions of the code didn't set Subscription.metadata and
            # used the Session.client_reference_id field instead.  Keep it work
            # for old objects.
            logger.info('Missing user_id metadata, falling back to Session client_reference_id for Stripe Subscription {}'.format(stripe_subscription.id))
            checkout_sessions = stripe.checkout.Session.list(subscription=stripe_subscription)
            if not checkout_sessions['data']:
                logger.info('Subscription.get_or_create cannot find Checkout Session from Stripe Subscription {}'.format(stripe_subscription.id))
                return None # no Checkout session associated with subscription yet
            user_id = json.loads(checkout_sessions['data'][0].client_reference_id)['user_id']
        user_id = int(user_id)

        user = User.objects.get(pk=user_id)
        plan = Plan.objects.get(stripe_plan_id=stripe_subscription.plan.id)

        now_active = stripe_subscription.status in ('active', 'trialing')
        now_canceled = stripe_subscription.cancel_at is not None

        subscription, created = Subscription.objects.get_or_create(
                stripe_subscription_id=stripe_subscription.id,
                defaults={
                    'user': user,
                    'plan': plan,
                    'stripe_customer_id': stripe_subscription.customer,
                    'expires': datetime.date.fromtimestamp(stripe_subscription.current_period_end),
                    'active': now_active,
                    'canceled': now_canceled,
                    'ip_country': GeoIP().country_code(user.userprofile.last_ip) or '',
                })

        if not subscription.billing_country or not subscription.card_country:
            subscription.refresh_country()

        was_active = False if created else subscription.active
        was_canceled = False if created else subscription.canceled

        if now_active != was_active:
            subscription.active = now_active
            subscription.save()

            if now_active:
                logger.info('Subscribing user {} to plan {} with Stripe Subscription {}'.format(user.username, plan.name, stripe_subscription.id))
                is_trialing = stripe_subscription.status == 'trialing'
                signals.user_subscribed.send(subscription, is_trialing=is_trialing)

            # TODO no signal is sent when a subscription becomes inactive due
            # to failed payments, so the user remains a premium subscriber!

        if now_canceled and not was_canceled:
            logger.info('Canceling subscription by user {} to plan {} with Stripe Subscription {}'.format(user.username, plan.name, stripe_subscription.id))
            subscription.canceled = now_canceled
            subscription.save()

            if now_canceled:
                signals.renewal_canceled.send(subscription)

        return subscription

    def refresh_country(self):
        payment_method = self.get_payment_method()
        if not payment_method:
            return # no cards attached yet

        self.billing_country = payment_method['billing_details']['address']['country']
        self.card_country = payment_method['card']['country']
        self.save()

        tax_rate = get_tax_rate_by_country_code(self.get_tax_country())
        if tax_rate is not None:
            stripe.Subscription.modify(self.stripe_subscription_id, default_tax_rates=[tax_rate.id])

    def get_tax_country(self):
        if not self.billing_country or not self.card_country:
            return ''
        a, b, c = sorted([self.ip_country, self.billing_country, self.card_country])
        if a == b:
            return a
        elif b == c:
            return b
        else:
            return self.billing_country

    def get_payment_method(self):
        '''Get the currently active stripe.PaymentMethod or None if it does not exist'''
        try:
            stripe_subscription = stripe.Subscription.retrieve(self.stripe_subscription_id)
        except:
            logger.exception(f'Failed to retrieve Subscription {self.stripe_subscription_id} to get payment method')
            return None
        payment_method_id = stripe_subscription.default_payment_method
        if not payment_method_id:
            # Get the most recently-added credit card
            try:
                payment_methods = stripe.PaymentMethod.list(customer=self.stripe_customer_id, type='card')['data']
            except:
                logger.exception(f'Failed to retrieve PaymentMethods for Customer {self.stripe_customer_id}')
                return None
            if payment_methods:
                payment_method_id = sorted(payment_methods, key=lambda x: x['created'])[-1]['id']
        if not payment_method_id:
            return None
        return stripe.PaymentMethod.retrieve(payment_method_id)

    def get_card_last4(self):
        '''Get the last 4 digits of the currently active credit card or None if it does not exist'''
        payment_method = self.get_payment_method()
        if payment_method:
            return payment_method.card.last4
        else:
            return None

    def refresh_expiration(self):
        stripe_subscription = stripe.Subscription.retrieve(self.stripe_subscription_id)
        self.expires = datetime.date.fromtimestamp(stripe_subscription.current_period_end)
        self.save()

    def cancel_renewal(self):
        if self.canceled:
            return

        # A webhook will be invoked and we'll set self.canceled in Subscription.get_or_create()
        stripe.Subscription.modify(self.stripe_subscription_id, cancel_at_period_end=True)

    def update_payment_details(self, payment_method_id):
        try:
            stripe.Subscription.modify(self.stripe_subscription_id, default_payment_method=payment_method_id)
        except:
            logger.exception(f'Failed to modify default_payment_method for Stripe Subscription {self.stripe_subscription_id}')
            raise

        signals.payment_details_updated.send(self)

    def __str__(self):
        return 'Subscription for %s to %s until %s' % (self.user.username, self.plan.name, self.expires.isoformat())


class Invoice(models.Model):
    '''Payment invoice'''
    stripe_invoice_id = models.CharField(max_length=255, help_text='Stripe Invoice ID', unique=True)
    seq_num = models.PositiveIntegerField(default=1)
    user = models.ForeignKey(User, on_delete=PROTECT)
    date = models.DateTimeField()
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=3)
    paid = models.BooleanField()
    refunded = models.BooleanField(default=False)
    tax_country = models.CharField(max_length=2, blank=True)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=decimal.Decimal(0))

    @staticmethod
    def get_or_create(stripe_invoice):
        stripe_subscription = stripe.Subscription.retrieve(stripe_invoice.subscription)
        subscription = Subscription.get_or_create(stripe_subscription)
        if subscription is None:
            logger.info('Invoice.get_or_create failed, unable to get Subscription for Stripe Subscription {}'.format(stripe_subscription.id))
            return None

        # This is not atomic but invoices are billed monthly, so the per-user
        # sequence number should not suffer races.  In the worse case create
        # will fail with an integrity error because seq_no is unique.
        def next_seq_num():
            try:
                latest = Invoice.objects.filter(user=subscription.user).latest('date')
                return latest.seq_num + 1
            except Invoice.DoesNotExist:
                return 1

        try:
            invoice, created = Invoice.objects.get_or_create(
                    stripe_invoice_id=stripe_invoice.id,
                    defaults={
                        'seq_num': next_seq_num,
                        'user': subscription.user,
                        'date': stripe_timestamp_to_datetime(stripe_invoice.created),
                        'amount': stripe_amount_to_decimal(stripe_invoice.amount_due),
                        'currency': stripe_invoice.currency,
                        'paid': False,
                    })
        except IntegrityError:
            # Just in case atomicity didn't work
            created = False
            invoice = Invoice.objects.get(stripe_invoice_id=stripe_invoice.id)

        if not invoice.tax_country:
            tax_country = subscription.get_tax_country()
            if tax_country:
                invoice.tax_country = tax_country
                tax_rate = get_tax_rate_by_country_code(tax_country)
                if tax_rate is not None:
                    invoice.tax_percentage = decimal.Decimal(tax_rate.percentage)
                invoice.save()

        return invoice

    def pay(self):
        self.paid = True
        self.save()

        stripe_invoice = stripe.Invoice.retrieve(self.stripe_invoice_id)

        subscription = Subscription.objects.get(stripe_subscription_id=stripe_invoice.subscription)
        subscription.refresh_expiration()

        billing_details = None
        payment_method = subscription.get_payment_method()
        if payment_method:
            billing_details = payment_method['billing_details']

        signals.invoice_paid.send(self, subscription=subscription, billing_details=billing_details)

    def refund(self):
        self.refunded = True
        self.save()

    def __str__(self):
        status = 'Unpaid'
        if self.paid:
            status = 'Paid'
        if self.refunded:
            status = 'Refunded'

        return '%s invoice #%d for %g %s by %s at %s' % (
                status,
                self.seq_num,
                self.amount,
                self.currency,
                self.user.username,
                self.date.strftime('%Y-%m-%d %H:%M'))


def handle_charge_refunded(stripe_event):
    stripe_charge = stripe_event['data']['object']
    if stripe_charge.refunded:
        stripe_invoice = stripe.Invoice.retrieve(stripe_charge.invoice)
        invoice = Invoice.get_or_create(stripe_invoice)
        invoice.refund()
        logger.info('charge.refunded {}'.format(invoice))


def handle_subscription(checkout_session):
    try:
        stripe_subscription = stripe.Subscription.retrieve(checkout_session.subscription)
    except:
        logger.exception('Failed to retrieve Stripe Subscription {} while subscribing'.format(checkout_session.subscription))
        raise

    try:
        subscription = Subscription.get_or_create(stripe_subscription)
    except:
        logger.exception('Subscription failed')
        raise


def handle_payment_details_update(checkout_session):
    try:
        setup_intent = stripe.SetupIntent.retrieve(checkout_session.setup_intent)
    except:
        logger.exception(f'Failed to retrieve Stripe SetupIntent {checkout_session.setup_intent}')
        raise

    # Sanity check that this event was actually supposed to update payment details
    if setup_intent.metadata.get('reason') != 'payment_details_update':
        logger.info('checkout.session.completed webhook event with mode="setup" but setup_intent.metadata.reason != "payment_details_update"')
        return

    try:
        stripe_subscription = stripe.Subscription.retrieve(setup_intent.metadata.subscription_id)
    except:
        logger.exception(f'Failed to retrieve Stripe Subscription {setup_intent.metadata.subscription_id} while updating payment details')
        raise

    try:
        subscription = Subscription.get_or_create(stripe_subscription)
    except:
        logger.exception('Subscription failed during payment details update')
        raise

    subscription.update_payment_details(setup_intent.payment_method)


def handle_checkout_session_completed(stripe_event):
    checkout_session = stripe_event['data']['object']

    if checkout_session.mode == 'subscription':
        handle_subscription(checkout_session)
    elif checkout_session.mode == 'setup':
        handle_payment_details_update(checkout_session)
    else:
        logger.warning(f'Unhandled checkout.session.completed webhook event: {stripe_event}')


def handle_customer_subscription_updated(stripe_event):
    stripe_subscription = stripe_event['data']['object']

    try:
        subscription = Subscription.get_or_create(stripe_subscription)
    except:
        logger.exception('Failed to get or create subscription for customer.subscription.updated')
        raise

    if stripe_subscription.status == 'past_due':
        # Handle payment failure manually for now.  In the future this can be
        # automated.
        user = subscription.user
        mail_admins('Subscription past due for user "{}"'.format(user.username),
                    'The subscription was not paid on time by user "{}" ({}).  Their subscription has been deactivated.  Please ask them to renew the subscription.'.format(user.username, user.email))


def handle_customer_subscription_deleted(stripe_event):
    stripe_subscription = stripe_event['data']['object']
    subscription = Subscription.get_or_create(stripe_subscription)
    signals.user_unsubscribed.send(subscription)


def handle_invoice_created_or_updated(stripe_event):
    stripe_invoice = stripe_event['data']['object']

    # Refresh the Invoice object to set the tax rate
    Invoice.get_or_create(stripe_invoice)


def handle_invoice_payment_succeeded(stripe_event):
    stripe_invoice = stripe_event['data']['object']

    logger.info('invoice.payment_succeeded for stripe_invoice_id {} paid {}'.format(stripe_invoice.id, stripe_invoice.paid))

    invoice = Invoice.get_or_create(stripe_invoice)
    if invoice is not None and stripe_invoice.paid:
        invoice.pay()
    else:
        logger.info('Did not pay Stripe Invoice {}'.format(stripe_invoice.id))


def handle_stripe_event(payload, sig_header):
    stripe_event = stripe.Webhook.construct_event(payload,
            sig_header, settings.STRIPE_WEBHOOK_SECRET)

    logger.info('Stripe "{}" event {}'.format(stripe_event.type, stripe_event.id))

    events_to_email_about = ('charge.failed',
            'charge.dispute.created', 'charge.dispute.updated',
            'charge.dispute.closed', 'invoice.payment_failed',
            'transfer.failed')
    if stripe_event.type in events_to_email_about:
        mail_admins('Stripe "%s" event' % stripe_event.type,
                    'The following Stripe event was sent to the webhook:\n%s' % str(stripe_event))

    if stripe_event.type == 'charge.refunded':
        handle_charge_refunded(stripe_event)
    elif stripe_event.type == 'checkout.session.completed':
        handle_checkout_session_completed(stripe_event)
    elif stripe_event.type == 'customer.subscription.updated':
        handle_customer_subscription_updated(stripe_event)
    elif stripe_event.type == 'customer.subscription.deleted':
        handle_customer_subscription_deleted(stripe_event)
    elif stripe_event.type in ('invoice.created', 'invoice.updated'):
        handle_invoice_created_or_updated(stripe_event)
    elif stripe_event.type == 'invoice.payment_succeeded':
        handle_invoice_payment_succeeded(stripe_event)


def offer_free_trial(user, plan):
    '''Is a free trial available?'''
    if user.is_authenticated():
        cutoff_date = datetime.date.today() - datetime.timedelta(6 * 4 * 7 - plan.trial_period_days)
        if Subscription.objects.filter(user=user, expires__gte=cutoff_date, canceled=True).exists():
            return False
    return True


def create_checkout_session(user, plan):
    '''Returns the Stripe Checkout Session ID so a given user can purchase the given plan'''
    domain = get_current_site(None).domain
    success_url = 'https://{}{}'.format(domain, reverse('payments-success'))
    cancel_url = 'https://{}{}'.format(domain, reverse('profiles_edit_profile'))

    session = stripe.checkout.Session.create(
        billing_address_collection='required',
        payment_method_types=['card'],
        subscription_data={
            'items': [{
                'plan': plan.stripe_plan_id,
            }],
            'metadata': {
                'user_id': user.id,
            },
            'trial_from_plan': offer_free_trial(user, plan),
        },
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session.id


def create_checkout_session_for_payment_details_update(subscription):
    '''Returns the Stripe Checout Session ID for updating payment details'''
    domain = get_current_site(None).domain
    success_url = 'https://{}{}'.format(domain, reverse('payments-update-success'))
    cancel_url = 'https://{}{}'.format(domain, reverse('profiles_edit_profile'))

    session = stripe.checkout.Session.create(
        billing_address_collection='required',
        payment_method_types=['card'],
        mode='setup',
        customer=subscription.stripe_customer_id,
        setup_intent_data={
            'metadata': {
                'reason': 'payment_details_update',
                'user_id': subscription.user.id,
                'subscription_id': subscription.stripe_subscription_id,
            },
        },
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session.id
