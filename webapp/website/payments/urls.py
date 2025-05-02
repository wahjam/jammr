# Copyright (C) 2014-2020 Stefan Hajnoczi <stefanha@gmail.com>

from django.conf.urls import url
from django.conf import settings
from django.views.generic.base import RedirectView
from . import views


urlpatterns = [
    url(r'^payments/manage$', views.ManagementView.as_view(), name='payments-manage'),
    url(r'^payments/subscribe$', RedirectView.as_view(url='/'), name='payments-subscribe'),
    url(r'^payments/subscribe/(?P<plan>\d+)/$', views.SubscriptionView.as_view(), name='payments-subscribe-with-plan'),
    url(r'^payments/success$', views.SuccessView.as_view(), name='payments-success'),
    url(r'^payments/update$', views.UpdatePaymentDetailsView.as_view(), name='payments-update'),
    url(r'^payments/update-success$', views.UpdatePaymentDetailsSuccessView.as_view(), name='payments-update-success'),
    url(r'^payments/cancel-renewal$', views.RenewalCancelationView.as_view(), name='payments-cancel-renewal'),
    url(r'^payments/stripe-webhook/{}$'.format(settings.STRIPE_WEBHOOK_NAME), views.WebhookView.as_view()),
]
