# Copyright 2012-2020 Stefan Hajnoczi <stefanha@gmail.com>

import datetime
import json
import logging
from django import forms
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver
from django.forms import ModelForm, TextInput
from django.forms.extras.widgets import SelectDateWidget
from django.core.urlresolvers import reverse_lazy
from django.utils.safestring import mark_safe
from registration.forms import RegistrationFormUniqueEmail
from registration.signals import user_registered, user_activated
from . import models
from . import fields

logger = logging.getLogger('website.forms')

class RegistrationForm(RegistrationFormUniqueEmail):
    # Override username field to forbid non-ASCII
    username = forms.RegexField(regex=r'\A[a-zA-Z0-9.+\-_]+\Z',
                                max_length=30,
                                label='Username',
                                help_text='The public username others will see.',
                                error_messages={'invalid': 'Usernames cannot contain spaces or be an email address.  Please use only letters, numbers and ./+/-/_ characters.'})

    # Override email address to remove help_text that clutters the HTML
    email = forms.EmailField()

    email2 = forms.EmailField(label='Email confirmation', help_text='Enter the same email as before, for verification.')

    mail_optin = forms.BooleanField(label='Email me news about jammr', required=False)
    policy_agreed = forms.BooleanField(error_messages={'required': 'Please agree to the Terms & Conditions and Privacy Policy to sign up'})
    captcha = fields.RecaptchaField(label='CAPTCHA')

    class Meta(RegistrationFormUniqueEmail.Meta):
        fields = (
            User.USERNAME_FIELD,
            'email',
            'email2',
            'password1',
            'password2',
            'mail_optin',
            'policy_agreed',
            'captcha',
        )

    def __init__(self, **kwargs):
        super(RegistrationForm, self).__init__(**kwargs)
        self.fields['policy_agreed'].label = mark_safe('I agree to the <a href="%s">Terms &amp; Conditions</a> and <a href="%s">Privacy Policy</a>' % (
                reverse_lazy('terms'),
                reverse_lazy('privacy')
            ))

    def clean_email2(self):
        email = self.cleaned_data.get('email')
        email2 = self.cleaned_data.get('email2')
        if email and email2 and email != email2:
            raise forms.ValidationError(
                "The two email fields didn't match.",
                code='email_mismatch',
            )
        return email2

@receiver(user_registered, dispatch_uid='populate_user_from_form')
def populate_user_from_form(sender, **kwargs):
    user, request = kwargs['user'], kwargs['request']
    form = RegistrationForm(data=request.POST)

    profile = models.UserProfile()
    profile.user = user
    profile.last_ip = request.META.get('REMOTE_ADDR', None)
    if 'mail_optin' in form.data:
        profile.mail_optin = True
    profile.save()

    logger.info('User "%s" signed up' % user.username)

@receiver(user_activated, dispatch_uid='activate_user')
def activate_user(sender, **kwargs):
    user, request = kwargs['user'], kwargs['request']

    content_type = ContentType.objects.get_for_model(User)
    permission = Permission.objects.get(content_type=content_type, codename='can_join_private_jams')
    user.user_permissions.add(permission)
    user.save()

    logger.info('User "%s" activated account' % user.username)

class EditProfileForm(ModelForm):
    class Meta:
        model = models.UserProfile
        fields = ('email_recorded_jams', 'instruments', 'influences')
        widgets = {'instruments': TextInput()}
