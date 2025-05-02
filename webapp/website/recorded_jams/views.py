# Copyright (C) 2013-2020 Stefan Hajnoczi <stefanha@gmail.com>

import datetime
import logging
import urllib.parse
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.contrib.auth.views import redirect_to_login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.timezone import utc
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.validators import URLValidator
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseRedirect
from .models import RecordedJam
from website.utils import http_basic_auth, render_json, RestApiView

logger = logging.getLogger('website.recorded_jams.views')

ISO8601_DATETIME_FMT = '%Y-%m-%dT%H:%MZ'
ISO8601_TIME_FMT = '%H:%M:%S'


class RecordedJamListView(ListView):
    model = RecordedJam
    paginate_by = 25

    def get_queryset(self):
        username = self.request.GET.get('username', None)
        if username:
            qs = RecordedJam.objects.filter(users__pk=self.request.user.pk).filter(users__username__icontains=username)
        else:
            qs = self.request.user.recorded_jams.all()
        return qs.order_by('-start_date')

    def get_context_data(self, **kwargs):
        username = self.request.GET.get('username', None)
        if username:
            get_params = 'username=' + urllib.parse.quote_plus(username) + '&'
        else:
            get_params = ''

        context = {
            'get_params': get_params,
            'username': username
        }
        context.update(**kwargs)
        return super(ListView, self).get_context_data(**context)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        if not self.request.user.has_perm('recorded_jams.can_access_recorded_jams'):
            raise PermissionDenied
        return super(ListView, self).dispatch(*args, **kwargs)


class RecordedJamDetailView(DetailView):
    model = RecordedJam

    def get_context_data(self, **kwargs):
        context = super(RecordedJamDetailView, self).get_context_data(**kwargs)
        context['can_download_tracks'] = context['object'].can_user_download_tracks(self.request.user)
        return context

    def render_to_response(self, context, **response_kwargs):
        jam = self.object
        request = self.request

        if not jam.can_user_access(request.user):
            if not request.user.is_authenticated():
                return redirect_to_login(request.path)
            raise PermissionDenied

        return super(DetailView, self).render_to_response(context, **response_kwargs)


class CanAccessRecordedJamApiView(RestApiView):
    http_method_names = ['get']

    @http_basic_auth()
    def get(self, request):
        # Only users that can also add recorded jams may access this API
        if not request.user.has_perm('recorded_jams.add_recordedjam'):
            logger.error('User \'{}\' does not have permission to check who can access recorded jams'.format(request.user.username))
            return HttpResponseForbidden('Forbidden')

        for username in request.GET.getlist('u'):
            try:
                user = User.objects.get(username__exact=username)
            except User.DoesNotExist:
                logger.error('User \'{}\' does not exist in CanAccessRecordedJamApiView'.format(username))
                return HttpResponseBadRequest('Bad Request')

            if user.has_perm('recorded_jams.can_access_recorded_jams'):
                return render_json(True)

        return render_json(False)


class RecordedJamApiView(RestApiView):
    http_method_names = ['post']

    @http_basic_auth()
    def post(self, request):
        if not request.user.has_perm('recorded_jams.add_recordedjam'):
            logger.error('User \'%s\' does not have permission to add recorded jams' % request.user.username)
            return HttpResponseForbidden('Forbidden')

        required_fields = ('start_date', 'users', 'mix_url', 'tracks_url', 'duration', 'server')
        for k in required_fields:
            if k not in request.POST:
                logger.error('Missing required %s field' % k)
                return HttpResponseBadRequest('Bad Request')

        try:
            start_date = datetime.datetime.strptime(request.POST['start_date'], ISO8601_DATETIME_FMT).replace(tzinfo=utc)
        except ValueError:
            logger.error('Invalid start date')
            return HttpResponseBadRequest('Bad Request')

        try:
            duration = datetime.datetime.strptime(request.POST['duration'], ISO8601_TIME_FMT).time()
        except ValueError:
            logger.error('Invalid duration')
            return HttpResponseBadRequest('Bad Request')

        if 'owner' in request.POST:
            try:
                owner = User.objects.get(username__exact=request.POST['owner'])
            except ObjectDoesNotExist:
                logger.error('Invalid username \'%s\' for owner' % request.POST['owner'])
                return HttpResponseBadRequest('Bad Request')
        else:
            owner = None

        users = []
        for username in request.POST.getlist('users'):
            try:
                users.append(User.objects.get(username__exact=username))
            except ObjectDoesNotExist:
                logger.error('Invalid username \'%s\' in users list' % username)
                return HttpResponseBadRequest('Bad Request')

        for k in ('mix_url', 'tracks_url'):
            try:
                URLValidator()(request.POST[k])
            except ValidationError:
                logger.error('URL validation failed for %s field' % k)
                return HttpResponseBadRequest('Bad Request')

        server = request.POST['server']
        if len(server) > 128:
            logger.error('Server string must be 128 characters or less')
            return HttpResponseBadRequest('Bad Request')

        jam = RecordedJam.objects.create(start_date=start_date,
                                         mix_url=request.POST['mix_url'],
                                         tracks_url=request.POST['tracks_url'],
                                         duration=duration,
                                         server=server,
                                         owner=owner)
        jam.users.add(*users)
        jam.email_users()
        return HttpResponse('Created', status=201)
