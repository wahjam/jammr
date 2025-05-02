# Copyright (C) 2015-2020 Stefan Hajnoczi <stefanha@gmail.com>

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def currency_symbol(value):
    '''Replaces currency codes with symbols'''
    symbols = {
        'eur': '€',
        'gbp': '£',
        'usd': '$',
    }
    return mark_safe(symbols.get(value, value))
