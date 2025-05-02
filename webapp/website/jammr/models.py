# Copyright 2012-2020 Stefan Hajnoczi <stefanha@gmail.com>

import decimal
import os
import logging
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Permission
from django.contrib.auth.signals import user_logged_in
from django.contrib.sites.models import Site
from website.utils import send_html_template_email
import website.payments.signals

logger = logging.getLogger('website.models')

SUBSCRIPTION_FREE = 0
SUBSCRIPTION_PREMIUM = 1

SUBSCRIPTION_CHOICES = (
    (SUBSCRIPTION_FREE, 'Free'),
    (SUBSCRIPTION_PREMIUM, 'Premium'),
)

def update_last_ip(sender, request, user, **kwargs):
    try:
        profile = user.userprofile
    except UserProfile.DoesNotExist:
        return
    profile.last_ip = request.META.get('REMOTE_ADDR', None)
    profile.save()
user_logged_in.connect(update_last_ip)

def user_subscribed(sender, **kwargs):
    user = sender.user

    content_type = ContentType.objects.get_for_model(User)
    permission = Permission.objects.get(content_type=content_type, codename='can_create_private_jams')
    user.user_permissions.add(permission)
    permission = Permission.objects.get_by_natural_key('can_download_tracks', 'recorded_jams', 'recordedjam')
    user.user_permissions.add(permission)
    permission = Permission.objects.get_by_natural_key('can_access_recorded_jams', 'recorded_jams', 'recordedjam')
    user.user_permissions.add(permission)
    user.save()

    user.userprofile.subscription = SUBSCRIPTION_PREMIUM
    user.userprofile.save()

    send_html_template_email([user.email],
                             'payments/user_subscribed',
                             { 'user': user,
                               'subscription': sender,
                               'domain': Site.objects.get_current().domain,
                               'is_trialing': kwargs.get('is_trialing', False) })
website.payments.signals.user_subscribed.connect(user_subscribed,
                                                 dispatch_uid='jammr_user_subscribed')

# Disable unsubcription for jammr shutdown period
# def user_unsubscribed(sender, **kwargs):
#     user = sender.user
# 
#     user.userprofile.subscription = SUBSCRIPTION_FREE
#     user.userprofile.save()
# 
#     content_type = ContentType.objects.get_for_model(User)
#     permission = Permission.objects.get(content_type=content_type, codename='can_create_private_jams')
#     user.user_permissions.remove(permission)
#     permission = Permission.objects.get_by_natural_key('can_download_tracks', 'recorded_jams', 'recordedjam')
#     user.user_permissions.remove(permission)
#     permission = Permission.objects.get_by_natural_key('can_access_recorded_jams', 'recorded_jams', 'recordedjam')
#     user.user_permissions.remove(permission)
#     user.save()
# 
#     send_html_template_email([user.email],
#                              'payments/user_unsubscribed',
#                              { 'user': user,
#                                'domain': Site.objects.get_current().domain})
# website.payments.signals.user_unsubscribed.connect(user_unsubscribed,
#                                                    dispatch_uid='jammr_user_unsubscribed')

def renewal_canceled(sender, **kwargs):
    send_html_template_email([sender.user.email],
                             'payments/renewal_canceled',
                             { 'user': sender.user,
                               'subscription': sender })
website.payments.signals.renewal_canceled.connect(renewal_canceled,
                                              dispatch_uid='jammr_renewal_canceled')

def invoice_paid(sender, **kwargs):
    pre_tax_amount = sender.amount / ((decimal.Decimal(100) + sender.tax_percentage) / decimal.Decimal(100))
    pre_tax_amount = pre_tax_amount.quantize(decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP)
    tax_amount = sender.amount - pre_tax_amount

    send_html_template_email(
            [sender.user.email],
            'payments/invoice_paid',
            {
                'domain': Site.objects.get_current().domain,
                'invoice': sender,
                'subscription': kwargs['subscription'],
                'billing_details': kwargs['billing_details'],
                'pre_tax_amount': pre_tax_amount,
                'tax_amount': tax_amount,
                'user': sender.user,
            })
website.payments.signals.invoice_paid.connect(invoice_paid,
                                              dispatch_uid='jammr_invoice_paid')

def payment_details_updated(sender, **kwargs):
    send_html_template_email(
            [sender.user.email],
            'payments/payment_details_updated',
            { 'domain': Site.objects.get_current().domain,
              'user': sender.user,
              'subscription': sender })
website.payments.signals.payment_details_updated.connect(payment_details_updated,
                                                         dispatch_uid='jammr_payment_details_updated')

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    subscription = models.SmallIntegerField(default=SUBSCRIPTION_FREE, choices=SUBSCRIPTION_CHOICES)
    instruments = models.TextField(max_length=80, blank=True)
    influences = models.TextField(max_length=256, blank=True)
    last_ip = models.GenericIPAddressField()
    email_recorded_jams = models.BooleanField(default=True)
    mail_optin = models.BooleanField(default=False)

    @models.permalink
    def get_absolute_url(self):
        return ('profiles_profile_detail', (), {'username': self.user.username})

    def soft_delete(self):
        """Remove personal information"""
        user = self.user

        logging.info('Soft deleting user "{}"'.format(user.username))

        try:
            subscriptions = user.subscription_set.filter(active=True)
        except:
            subscriptions = []
        for s in subscriptions:
            s.cancel_renewal()

        self.instruments = ''
        self.influences = ''
        self.last_ip = '127.0.0.1'
        self.email_recorded_jams = False
        self.mail_optin = False
        self.save()

        user.first_name = ''
        user.last_name = ''
        user.email = ''
        user.is_active = False
        user.save()

        user.subscriptions.clear() # DjangoBB subscriptions, not payment subscriptions

        for post in user.posts.all():
            post.body = 'Deleted'
            post.body_html = 'Deleted'
            post.user_ip = ''
            post.save()

            attachments = list(post.attachments.all())
            for attachment in attachments:
                try:
                    os.unlink(attachment.get_absolute_path())
                except OSError:
                    pass
                attachment.delete()

        forum_profile = user.forum_profile
        forum_profile.status = ''
        forum_profile.site = ''
        forum_profile.jabber = ''
        forum_profile.icq = ''
        forum_profile.msn = ''
        forum_profile.aim = ''
        forum_profile.yahoo = ''
        forum_profile.location = ''
        forum_profile.signature = ''
        forum_profile.signature_html = ''
        forum_profile.avatar.delete() # automatically saves
