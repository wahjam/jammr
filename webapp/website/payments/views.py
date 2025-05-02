# Copyright (C) 2014-2020 Stefan Hajnoczi <stefanha@gmail.com>

import logging
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.forms import Form
from django.views.generic import TemplateView, ListView
from django.views.generic.edit import FormView
from django.shortcuts import redirect
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseServerError
from django.conf import settings
from django.contrib.gis.geoip import GeoIP
from website.utils import RestApiView
from . import models

logger = logging.getLogger('website.payments.views')


def get_active_subscription(user):
    try:
        return user.subscription_set.get(active=True)
    except models.Subscription.DoesNotExist:
        return None


class ManagementView(ListView):
    template_name = 'payments/manage.html'
    paginate_by = 10

    def get_queryset(self):
        return self.request.user.invoice_set.order_by('-date')

    def get_context_data(self, **kwargs):
        context = super(ManagementView, self).get_context_data(**kwargs)
        context['subscription'] = get_active_subscription(self.request.user)
        return context

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ManagementView, self).dispatch(*args, **kwargs)


class SubscriptionView(FormView):
    template_name = 'payments/subscribe.html'
    form_class = Form

    def get_country_code(self):
        if 'REMOTE_ADDR' not in self.request.META:
            return ''
        return GeoIP().country_code(self.request.META['REMOTE_ADDR'])

    def get_plan(self):
        if 'plan' in self.kwargs:
            try:
                return models.Plan.objects.get(pk=int(self.kwargs['plan']), visible=True)
            except (ValueError, models.Plan.DoesNotExist):
                pass

        return models.Plan.get_plan_by_country_code(self.get_country_code())

    def get_context_data(self, **kwargs):
        user = self.request.user
        plan = self.get_plan()

        context = super(SubscriptionView, self).get_context_data(**kwargs)
        context['stripe_pub_key'] = getattr(settings, 'STRIPE_PUB_KEY', '')
        context['plans'] = models.Plan.objects.filter(visible=True)
        context['plan'] = plan
        context['offer_free_trial'] = models.offer_free_trial(user, plan)
        context['checkout_session_id'] = kwargs.get('checkout_session_id')
        return context

    def form_valid(self, form):
        user = self.request.user
        if not user.is_authenticated():
            return HttpResponseForbidden('Forbidden')
        checkout_session_id = models.create_checkout_session(user, self.get_plan())
        context = self.get_context_data(form=form, checkout_session_id=checkout_session_id)
        return self.render_to_response(context)

    def dispatch(self, request, *args, **kwargs):
        if hasattr(request.user, 'subscription_set'):
            already_subscribed = request.user.subscription_set.filter(active=True).exists()
            if already_subscribed:
                return redirect('payments-manage')

        return super(SubscriptionView, self).dispatch(request, *args, **kwargs)


class UpdatePaymentDetailsView(TemplateView):
    template_name = 'payments/update.html'

    def get_context_data(self, **kwargs):
        context = super(UpdatePaymentDetailsView, self).get_context_data(**kwargs)
        context['stripe_pub_key'] = getattr(settings, 'STRIPE_PUB_KEY', '')
        context['checkout_session_id'] = kwargs.get('checkout_session_id')
        return context

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        subscription = get_active_subscription(request.user)
        if not subscription:
            logger.error(f'Attempt to update payment details from user "{request.user.username}" without subscription')
            return HttpResponseBadRequest()

        checkout_session_id = models.create_checkout_session_for_payment_details_update(subscription)
        kwargs['checkout_session_id'] = checkout_session_id
        return super(UpdatePaymentDetailsView, self).get(request, *args, **kwargs)


class UpdatePaymentDetailsSuccessView(TemplateView):
    template_name = 'payments/update_success.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UpdatePaymentDetailsSuccessView, self).dispatch(*args, **kwargs)


class RenewalCancelationView(TemplateView):
    http_method_names = ['post']
    template_name = 'payments/cancel_renewal.html'

    def post(self, request, *args, **kwargs):
        try:
            subscription = request.user.subscription_set.get(active=True)
        except models.Subscription.DoesNotExist:
            logger.error('Cannot cancel renewal for user "%s" without subscription' % request.user.username)
            return HttpResponseBadRequest()

        try:
            subscription.cancel_renewal()
        except:
            logger.exception('Failed to cancel renewal')
            return HttpResponseServerError()

        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(RenewalCancelationView, self).dispatch(*args, **kwargs)


class SuccessView(TemplateView):
    template_name = 'payments/success.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(SuccessView, self).dispatch(*args, **kwargs)


class WebhookView(RestApiView):
    def post(self, request):
        try:
            sig_header = request.META['HTTP_STRIPE_SIGNATURE']
            models.handle_stripe_event(request.body, sig_header)
        except:
            logger.exception('Stripe webhook failed while processing event')
            return HttpResponseBadRequest()

        return HttpResponse()
