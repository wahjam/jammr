# Copyright 2012-2020 Stefan Hajnoczi <stefanha@gmail.com>

from django.conf.urls import url, include
from django.views.generic import TemplateView, RedirectView
from registration.backends.model_activation.views import ActivationView
from registration.backends.model_activation.views import RegistrationView
from django.contrib.auth.views import LoginView, LogoutView, \
        PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, \
        PasswordResetCompleteView, PasswordChangeView, PasswordChangeDoneView
from . import views
from . import forms

urlpatterns = [
    url(r'^login/$', LoginView.as_view(), name='login'),
    url(r'^logout/$', LogoutView.as_view(), name='logout'),

    # Registration
    url(r'^accounts/register/$',
        RegistrationView.as_view(form_class=forms.RegistrationForm),
        name='registration_register'),
    url(r'^register/complete/$',
        TemplateView.as_view(template_name='registration/registration_complete.html'),
        name='registration_complete'),
    url(r'^register/closed/$',
        TemplateView.as_view(template_name='registration/registration_closed.html'),
        name='registration_disallowed'),
    url(r'^register/activate/complete/$',
        RedirectView.as_view(url='/login/?next=/profiles/edit/'),
        name='registration_activation_complete'),
    url(r'^register/activate/(?P<activation_key>\w+)/$',
        ActivationView.as_view(),
        name='registration_activate'),
    url(r'^accounts/', include('registration.auth_urls')),
    url(r'^accounts/password_reset/$',
        PasswordResetView.as_view(
            template_name='registration/jammr_password_reset_form.html',
            email_template_name='registration/jammr_password_reset_email.html',
            subject_template_name='registration/jammr_password_reset_subject.txt'),
        name='password_reset'),
    url(r'^accounts/password_reset/done/$',
        PasswordResetDoneView.as_view(template_name='registration/jammr_password_reset_done.html'),
        name='password_reset_done'),
    url(r'^accounts/reset/(?P<uidb64>[0-9A-Za-z_\-]+)-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        PasswordResetConfirmView.as_view(template_name='registration/jammr_password_reset_confirm.html'),
        name='password_reset_confirm'),
    url(r'^accounts/reset/done/$',
        PasswordResetCompleteView.as_view(template_name='registration/jammr_password_reset_complete.html'),
        name='password_reset_complete'),
    url(r'^accounts/password_change/$',
        PasswordChangeView.as_view(template_name='registration/jammr_password_change_form.html'),
        name='password_change'),
    url(r'^accounts/password_change/done/$',
        PasswordChangeDoneView.as_view(template_name='registration/jammr_password_change_done.html'),
        name='password_change_done'),

    # Profiles
    url(r'^profiles/edit/$', views.ProfileEditView.as_view(), name='profiles_edit_profile'),
    url(r'^accounts/delete/$', views.ProfileDeleteView.as_view(), name='profiles_delete_profile'),
    url(r'^accounts/deleted/$', views.ProfileDeletedView.as_view(), name='profiles_deleted'),
    url(r'^profiles/(?P<username>[a-zA-Z0-9@.+\-_]+)/$', views.ProfileDetailView.as_view(), name='profiles_profile_detail'),
    url(r'^users/(?P<username>[a-zA-Z0-9@.+\-_]+)/$', RedirectView.as_view(url='/profiles/%(username)s/')),

    url(r'^$', views.index),
    url(r'^index.html$', RedirectView.as_view(url='/', permanent=True)),
    url(r'^howitworks.html$', TemplateView.as_view(template_name='howitworks.html')),
    url(r'^faq.html$', TemplateView.as_view(template_name='faq.html')),
    url(r'^pricing.html$', RedirectView.as_view(url='/')),
    url(r'^download.html$', views.download),
    url(r'^about.html$', TemplateView.as_view(template_name='about.html')),
    url(r'^contact.html$', TemplateView.as_view(template_name='contact.html')),
    url(r'^opensource.html$', TemplateView.as_view(template_name='opensource.html')),
    url(r'^terms.html$', TemplateView.as_view(template_name='terms.html'), name='terms'),
    url(r'^privacy.html$', RedirectView.as_view(url='/privacy-02062023.html'), name='privacy'),
    url(r'^privacy-19052013.html$', TemplateView.as_view(template_name='privacy-19052013.html')),
    url(r'^privacy-25052018.html$', TemplateView.as_view(template_name='privacy-25052018.html')),
    url(r'^privacy-12042020.html$', TemplateView.as_view(template_name='privacy-12042020.html')),
    url(r'^privacy-02062023.html$', TemplateView.as_view(template_name='privacy-02062023.html')),
]
