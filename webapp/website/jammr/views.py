# Copyright 2012-2014 Stefan Hajnoczi <stefanha@gmail.com>

from django.forms import Form
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.urls import reverse_lazy
from django.views.generic import DetailView, TemplateView, UpdateView
from django.views.generic.edit import FormView
from website.utils import redis
from . import forms
from . import models


def download(request):
    user_agent = request.META.get('HTTP_USER_AGENT', 'Windows')
    if 'inux' in user_agent:
        platform = 'Linux'
    elif 'Mac OS X' in user_agent:
        platform = 'Mac OS X'
    else:
        platform = 'Windows'

    return render(request, 'download.html', {'platform': platform})


def index(request):
    try:
        n = int(redis.get('num_public_users'))
    except:
        n = 0 # just in case redis fails
    if n is None:
        n = 0 # key not present
    return render(request, 'index.html', {'num_public_users': n})


class ProfileDetailView(DetailView):
    model = models.UserProfile
    slug_field = 'user__username'
    slug_url_kwarg = 'username'
    context_object_name = 'profile'
    template_name = 'profiles/profile_detail.html'


class ProfileEditView(UpdateView):
    model = models.UserProfile
    form_class = forms.EditProfileForm
    context_object_name = 'profile'
    template_name = 'profiles/edit_profile.html'
    success_url = '/profiles/edit/'

    def get_object(self):
        return self.request.user.userprofile

    def get_context_data(self, **kwargs):
        context = {
            'can_access_recorded_jams': self.request.user.has_perm('recorded_jams.can_access_recorded_jams')
        }
        context.update(**kwargs)
        return super(UpdateView, self).get_context_data(**context)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProfileEditView, self).dispatch(*args, **kwargs)


class ProfileDeleteView(FormView):
    template_name = 'profiles/delete_profile.html'
    form_class = Form
    success_url = reverse_lazy('profiles_deleted')

    def get_context_data(self, **kwargs):
        context = super(ProfileDeleteView, self).get_context_data(**kwargs)
        context['has_subscription'] = self.request.user.subscription_set.filter(active=True).exists()
        return context

    def form_valid(self, form):
        self.request.user.userprofile.soft_delete()
        logout(self.request)
        return super(ProfileDeleteView, self).form_valid(form)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProfileDeleteView, self).dispatch(*args, **kwargs)


class ProfileDeletedView(TemplateView):
    template_name = 'profiles/deleted.html'
