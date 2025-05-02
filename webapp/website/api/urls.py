# Copyright 2012-2020 Stefan Hajnoczi <stefanha@gmail.com>

from django.conf.urls import url
from .views import TokenView, LivejamView, ACLView, UsernamesView

urlpatterns = [
    url(r'^tokens/(?P<username>[^/]+)/$', TokenView.as_view()),
    url(r'^livejams/$', LivejamView.as_view()),
    url(r'^acls/(?P<server>[^/]+)/$', ACLView.as_view()),
    url(r'^usernames/$', UsernamesView.as_view()),
]
