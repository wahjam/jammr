# Copyright (C) 2014-2018 Stefan Hajnoczi <stefanha@gmail.com>

import json
import logging
import sys
import urllib.request, urllib.parse, urllib.error
import socket
from django.core.exceptions import ValidationError
from django.core import validators
from django.http import HttpRequest
from django import forms
from django.conf import settings

logger = logging.getLogger('website.fields')

class RecaptchaWidget(forms.Widget):
    def __init__(self, attrs=None):
        super(RecaptchaWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        return '''<script type="text/javascript" src="https://www.google.com/recaptcha/api.js"></script>
                    <div class="g-recaptcha" data-sitekey="%(recaptcha_site_key)s"></div>''' % dict(recaptcha_site_key=self.attrs.get('recaptcha_site_key', ''))

    def value_from_datadict(self, data, files, name):
        return data.get('g-recaptcha-response')


class RecaptchaField(forms.Field):
    widget = RecaptchaWidget

    def __init__(self, *args, **kwargs):
        self.recaptcha_site_key = kwargs.get('recaptcha_site_key', getattr(settings, 'RECAPTCHA_SITE_KEY', ''))
        self.recaptcha_secret = kwargs.get('recaptcha_secret', getattr(settings, 'RECAPTCHA_SECRET', ''))
        super(RecaptchaField, self).__init__(validators=[self.validator], *args, **kwargs)

    def widget_attrs(self, widget):
        return {'recaptcha_site_key': self.recaptcha_site_key}

    def validator(self, response):
        if not response or response in validators.EMPTY_VALUES:
            raise ValidationError('Missing response field')

        # Get the remote IP, this is a hack but Django offers no easy way to
        # get the IP address from a Field.
        frame = sys._getframe()
        remoteip = None
        while frame:
            request = frame.f_locals.get('request', None)
            if request is not None and isinstance(request, HttpRequest):
                remoteip = request.META.get('REMOTE_ADDR', None)
                break
            frame = frame.f_back
        if remoteip is None:
            logger.error('Unable to find HttpRequest in RecaptchaField.compress()')
            raise ValidationError('Unable to validate captcha due to internal error')

        url = 'https://www.google.com/recaptcha/api/siteverify'
        form_data = urllib.parse.urlencode(dict(secret=self.recaptcha_secret,
                                          remoteip=remoteip,
                                          response=response)).encode('utf-8')
        logger.info('Validating captcha: %s' % url)

        success, error = False, ''

        try:
            timeout = 10 # seconds
            f = urllib.request.urlopen(url, form_data, timeout)
            result = json.load(f)
            logger.info('Response: %s' % repr(result))
            if result.get('success', False):
                success = True
            else:
                error = 'incorrect-captcha-sol'
        except socket.timeout:
            error = 'recaptcha-not-reachable'
        except urllib.error.HTTPError:
            error = 'incorrect-captcha-sol'
        except:
            logger.exception('Exception during captcha validation')
            error = 'incorrect-captcha-sol'

        logger.info('Finished validating captcha: success=%s error=%s' % (success, error))

        if not success:
            raise ValidationError('Captcha validation failed: %s' % error)
