# Copyright 2015-2020 Stefan Hajnoczi <stefanha@gmail.com>
from django.contrib import admin
from . import models


class SubscriptionAdmin(admin.ModelAdmin):
    search_fields = ('stripe_customer_id', 'stripe_subscription_id',
                     'user__username', 'user__email')
    raw_id_fields = ('user',)


class InvoiceAdmin(admin.ModelAdmin):
    search_fileds = ('stripe_invoice_id', 'user__username', 'user__email')
    raw_id_fields = ('user',)


admin.site.register(models.Invoice, InvoiceAdmin)
admin.site.register(models.Plan)
admin.site.register(models.Subscription, SubscriptionAdmin)
admin.site.register(models.TaxRateChange)
