# Copyright (C) 2013-2020 Stefan Hajnoczi <stefanha@gmail.com>

import base64
from django.contrib.auth.models import User, Permission
from django.test import TestCase
from website import jammr

AUTH = 'basic ' + base64.b64encode(b'recorded-jams:password').decode('utf-8')
ALEX_AUTH = 'basic ' + base64.b64encode(b'alex:password').decode('utf-8')
BAD_AUTH = 'basic ' + base64.b64encode(b'recorded-jams:passwordx').decode('utf-8')

DATA_TEMPLATE = {
    'start_date': '2013-07-16T05:28Z',
    'owner': 'alex',
    'users': ['alex', 'bob', 'chris'],
    'mix_url': 'http://test.jammr.net/mix.m4a',
    'tracks_url': 'http://test.jammr.net/secret/tracks.zip',
    'duration': '00:59:30',
    'server': 'dev1.jammr.net:10100',
}

class PostRecordedJamTestCase(TestCase):
    def setUp(self):
        u = User.objects.create_user('recorded-jams', 'test@example.org', 'password')
        p = Permission.objects.get(name='Can add recorded jam')
        u.user_permissions.add(p)

        u = User.objects.create_user('alex', 'test@example.org', 'password')
        jammr.models.UserProfile.objects.create(user=u, subscription=jammr.models.SUBSCRIPTION_PREMIUM, last_ip='192.168.0.1')
        u = User.objects.create_user('bob', 'test@example.org', 'password')
        jammr.models.UserProfile.objects.create(user=u, subscription=jammr.models.SUBSCRIPTION_FREE, last_ip='192.168.0.2')
        u = User.objects.create_user('chris', 'test@example.org', 'password')
        jammr.models.UserProfile.objects.create(user=u, subscription=jammr.models.SUBSCRIPTION_FREE, last_ip='192.168.0.3')

    def test_private_jam(self):
        response = self.client.post('/api/recorded-jams/',
                                    DATA_TEMPLATE,
                                    HTTP_AUTHORIZATION=AUTH)
        self.assertEqual(response.status_code, 201)

    def test_public_jam(self):
        data = dict(DATA_TEMPLATE)
        del data['owner']
        response = self.client.post('/api/recorded-jams/',
                                    data,
                                    HTTP_AUTHORIZATION=AUTH)
        self.assertEqual(response.status_code, 201)

    def test_missing_required_fields(self):
        for field in list(DATA_TEMPLATE.keys()):
            if field == 'owner': # this field is optional
                continue
            data = dict(DATA_TEMPLATE)
            del data[field]
            response = self.client.post('/api/recorded-jams/',
                                        data,
                                        HTTP_AUTHORIZATION=AUTH)
            self.assertEqual(response.status_code, 400)

    def test_not_authenticated(self):
        response = self.client.post('/api/recorded-jams/',
                                    DATA_TEMPLATE)
        self.assertEqual(response.status_code, 401)

    def test_wrong_password(self):
        response = self.client.post('/api/recorded-jams/',
                                    DATA_TEMPLATE,
                                    HTTP_AUTHORIZATION=BAD_AUTH)
        self.assertEqual(response.status_code, 401)

    def test_no_permission_to_create_recorded_jam(self):
        response = self.client.post('/api/recorded-jams/',
                                    DATA_TEMPLATE,
                                    HTTP_AUTHORIZATION=ALEX_AUTH)
        self.assertEqual(response.status_code, 403)

    def test_owner_does_not_exist(self):
        data = dict(DATA_TEMPLATE)
        data['owner'] = 'asdf'
        response = self.client.post('/api/recorded-jams/',
                                    data,
                                    HTTP_AUTHORIZATION=AUTH)
        self.assertEqual(response.status_code, 400)

    def test_user_does_not_exist(self):
        data = dict(DATA_TEMPLATE)
        data['users'] = ['asdf', 'alex']
        response = self.client.post('/api/recorded-jams/',
                                    data,
                                    HTTP_AUTHORIZATION=AUTH)
        self.assertEqual(response.status_code, 400)
