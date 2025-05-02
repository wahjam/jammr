# Copyright 2013-2020 Stefan Hajnoczi <stefanha@gmail.com>

from django.conf.urls import url
from .views import RecordedJamListView, RecordedJamDetailView, \
                   RecordedJamApiView, CanAccessRecordedJamApiView

urlpatterns = [
    url(r'^api/recorded-jams/$', RecordedJamApiView.as_view()),
    url(r'^api/can-access-recorded-jams/$', CanAccessRecordedJamApiView.as_view()),
    url(r'^recorded-jams/(?P<pk>\d+)/$', RecordedJamDetailView.as_view(), name='recorded_jam_view'),
    url(r'^recorded-jams/$', RecordedJamListView.as_view(), name='recorded_jam_list_view'),
]
