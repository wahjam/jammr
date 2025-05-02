# Copyright 2012-2020 Stefan Hajnoczi <stefanha@gmail.com>

import base64
import threading
import json
from functools import wraps
from django.conf import settings
from django.test.runner import DiscoverRunner
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.views.generic.base import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from redis import StrictRedis

# Ensure connections are not shared between threads
connections = threading.local()

def _get_redis_settings():
    return getattr(settings, 'REDIS', dict(host='127.0.0.1', port=6379,
        db=0, password=None, decode_responses=True))

class RedisProxy(object):
    def __getattr__(self, name):
        conn = getattr(connections, 'conn', None)
        if conn is None:
            conn = StrictRedis(**_get_redis_settings())
            setattr(connections, 'conn', conn)
        return getattr(conn, name)

    def mget_keys(self, pattern):
        '''MGET the values of keys matching a pattern'''
        keys = self.keys(pattern)
        if not keys:
            return () # MGET takes at least one key

        # Skip keys that were deleted between KEYS and MGET calls
        return (k for k in self.mget(keys) if k is not None)

redis = RedisProxy()

class RedisTestSuiteRunner(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        super(RedisTestSuiteRunner, self).setup_test_environment(**kwargs)

        self.old_conf = _get_redis_settings()
        conf = dict(self.old_conf)
        conf['db'] = 1
        setattr(settings, 'REDIS', conf)

        # Delete all keys in test database
        redis.flushdb()

    def teardown_test_environment(self, **kwargs):
        super(RedisTestSuiteRunner, self).teardown_test_environment(**kwargs)

        redis.flushdb()
        setattr(settings, 'REDIS', self.old_conf)

def render_json(data):
    '''Return HttpResponse from data as JSON'''
    return HttpResponse(json.dumps(data), content_type='application/json')

def http_basic_auth(realm='api', allow_anonymous=False):
    '''Method decorator for HTTP Basic Authentication'''
    def inner(view):
        @wraps(view)
        def dispatch(self, request, *args, **kwargs):
            def fail():
                if allow_anonymous:
                    return view(self, request, *args, **kwargs)
                response = HttpResponse('Not Authorized', status=401)
                response['WWW-Authenticate'] = 'Basic realm="%s"' % realm
                return response

            http_authorization = request.META.get('HTTP_AUTHORIZATION', '')
            if http_authorization.startswith('Basic ') or http_authorization.startswith('basic '):
                try:
                    # HTTP Basic authorization is supposed to be Latin-1
                    # according to RFC 2617, but in practice browsers do
                    # different things.
                    #
                    # We assume the caller is either using UTF-8 or ASCII (a
                    # subset of UTF-8).  Allow full UTF-8 because users might
                    # have non-ASCII characters in their passwords.  The jammr
                    # client uses UTF-8.
                    pair = base64.b64decode(http_authorization[len('Basic '):]).decode('utf-8')
                    username, password = pair.split(':', 1)
                except:
                    return fail()
                user = authenticate(username=username, password=password)
                if user and user.is_active:
                    login(request, user)
                    return view(self, request, *args, **kwargs)
            return fail()

        return dispatch

    return inner

class RestApiView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(RestApiView, self).dispatch(*args, **kwargs)

def send_html_template_email(to_list, template_prefix, context_data, connection=None):
    subject = render_to_string(template_prefix + '_subject.txt', context_data).rstrip()
    text_content = render_to_string(template_prefix + '_content.txt', context_data)
    html_content = render_to_string(template_prefix + '_content.html', context_data)

    msg = EmailMultiAlternatives(subject, text_content, None, to_list, connection=connection)
    msg.attach_alternative(html_content, 'text/html')
    msg.send()
