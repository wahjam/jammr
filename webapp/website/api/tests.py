# Copyright (C) 2012-2020 Stefan Hajnoczi <stefanha@gmail.com>

import base64
import json
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from website.utils import redis
from .models import AccessControlList

USERNAME = 'asdf'
PASSWORD = 'asdf'
EMAIL = 'asdf@sogetthis.com'
USERNAME2 = 'hjkl'
PASSWORD2 = 'hjkl'
EMAIL2 = 'hjkl@sogetthis.com'

class ApiTestCase(TestCase):
    AUTH = 'Basic ' + base64.b64encode((USERNAME + ':' + PASSWORD).encode('utf-8')).decode('utf-8')
    BAD_AUTH = 'Basic ' + base64.b64encode((USERNAME + ':' + PASSWORD + 'x').encode('utf-8')).decode('utf-8')

    fixtures = ['initial_data']

    def setUp(self):
        user = User.objects.create_user(USERNAME, EMAIL, PASSWORD)
        user.save()
        user = User.objects.create_user(USERNAME2, EMAIL2, PASSWORD2)
        user.save()
        redis.flushdb()

        self.client = Client()

    def tearDown(self):
        user = User.objects.get(username__exact=USERNAME)
        user.delete()
        user = User.objects.get(username__exact=USERNAME2)
        user.delete()
        redis.flushdb()

class TokenTest(ApiTestCase):
    TOKEN = '1234567890' * 4
    WAHJAMSRV_AUTH = 'Basic ' + base64.b64encode(b'wahjamsrv:IeY7Eegh').decode('utf-8')

    def test_get(self):
        # Success case
        redis.set('tokens/' + USERNAME, TokenTest.TOKEN)
        response = self.client.get('/api/tokens/%s/' % USERNAME,
                                   HTTP_AUTHORIZATION=TokenTest.WAHJAMSRV_AUTH)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['token'], TokenTest.TOKEN)
        redis.delete('tokens/' + USERNAME)

        # Missing can_read_token permissions
        redis.set('tokens/' + USERNAME, TokenTest.TOKEN)
        response = self.client.get('/api/tokens/%s/' % USERNAME,
                                   HTTP_AUTHORIZATION=self.AUTH)
        self.assertEqual(response.status_code, 403)
        redis.delete('tokens/' + USERNAME)

        # Username or token does not exist
        response = self.client.get('/api/tokens/invalid/',
                                   HTTP_AUTHORIZATION=TokenTest.WAHJAMSRV_AUTH)
        self.assertEqual(response.status_code, 404)

    def test_set(self):
        # Success case
        response = self.client.post('/api/tokens/%s/' % USERNAME,
                                    {'token': TokenTest.TOKEN},
                                    HTTP_AUTHORIZATION=self.AUTH)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(redis.get('tokens/' + USERNAME), TokenTest.TOKEN)
        redis.delete('tokens/' + USERNAME)

        # Token too long
        response = self.client.post('/api/tokens/%s/' % USERNAME,
                                    {'token': TokenTest.TOKEN * 2},
                                    HTTP_AUTHORIZATION=self.AUTH)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(redis.exists('tokens/' + USERNAME), False)

        # Invalid credentials
        response = self.client.post('/api/tokens/%s/' % USERNAME,
                                    {'token': TokenTest.TOKEN},
                                    HTTP_AUTHORIZATION=self.BAD_AUTH)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(redis.exists('tokens/' + USERNAME), False)

        # Trying to set another user's token
        response = self.client.post('/api/tokens/%s/' % USERNAME2,
                                    {'token': TokenTest.TOKEN},
                                    HTTP_AUTHORIZATION=self.AUTH)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(redis.exists('tokens/' + USERNAME), False)

class LivejamTest(ApiTestCase):
    def test_read(self):
        status = dict(server="127.0.0.1:10100", topic="Welcome!",
                users=["asdf", "hjkl"], numusers=2, maxusers=0,
                bpm=120, bpi=32)
        redis.set('livejams/127.0.0.1:10100', json.dumps(status))
        response = self.client.get('/api/livejams/', HTTP_AUTHORIZATION=self.AUTH)
        self.assertEqual(response.status_code, 200)
        livejams = json.loads(response.content)
        self.assertEqual(len(livejams), 1)
        self.assertEqual(livejams[0], status)

class AccessControlListModelTest(TestCase):
    def test_allow(self):
        acl = AccessControlList('alex', 'allow', ('bob', 'dave', 'mike'))
        self.assertTrue(acl.is_allowed('alex'))
        self.assertTrue(acl.is_allowed('mike'))
        self.assertTrue(acl.is_allowed('bob'))
        self.assertTrue(acl.is_allowed('dave'))
        self.assertFalse(acl.is_allowed('jim'))

    def test_block(self):
        acl = AccessControlList('alex', 'block', ('bob', 'dave', 'mike'))
        self.assertTrue(acl.is_allowed('alex'))
        self.assertFalse(acl.is_allowed('mike'))
        self.assertFalse(acl.is_allowed('bob'))
        self.assertFalse(acl.is_allowed('dave'))
        self.assertTrue(acl.is_allowed('jim'))

class AccessControlListHandlerTest(ApiTestCase):
    SERVER = '127.0.0.1:1234' # value doesn't matter
    AUTH2 = 'Basic ' + base64.b64encode((USERNAME2 + ':' + PASSWORD2).encode('utf-8')).decode('utf-8')

    def test_get(self):
        # Success case
        acl = AccessControlList(USERNAME, 'block', ('bob', 'dave', 'mike'))
        acl_json = json.dumps(acl.to_dict())
        redis.set('acls/' + self.SERVER, acl_json)
        response = self.client.get('/api/acls/%s/' % self.SERVER,
                                   HTTP_AUTHORIZATION=self.AUTH)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        new_acl = AccessControlList.from_dict(data)
        self.assertEqual(acl, new_acl)

        # Does not own ACL
        response = self.client.get('/api/acls/%s/' % self.SERVER,
                                   HTTP_AUTHORIZATION=self.AUTH2)
        self.assertEqual(response.status_code, 403)
        redis.delete('acls/' + self.SERVER)

        # Username or token does not exist
        response = self.client.get('/api/acls/invalid/',
                                   HTTP_AUTHORIZATION=self.AUTH)
        self.assertEqual(response.status_code, 404)

    def test_set(self):
        # Success case
        acl = AccessControlList(USERNAME, 'block', ('bob', 'dave', 'mike'))
        acl_json = json.dumps(acl.to_dict())
        redis.set('acls/' + self.SERVER, acl_json)
        response = self.client.post('/api/acls/%s/' % self.SERVER,
                                    {'mode': 'allow',
                                     'usernames': ('bob', 'mike')},
                                    HTTP_AUTHORIZATION=self.AUTH)
        self.assertEqual(response.status_code, 201)
        data = json.loads(redis.get('acls/' + self.SERVER))
        new_acl = AccessControlList.from_dict(data)
        self.assertEqual(new_acl,
                AccessControlList(USERNAME, 'allow', ('bob', 'mike')))
        redis.delete('acls/' + self.SERVER)

        # Invalid credentials
        response = self.client.post('/api/acls/%s/' % self.SERVER,
                                    {'mode': 'allow',
                                     'usernames': ('bob', 'mike')},
                                    HTTP_AUTHORIZATION=self.BAD_AUTH)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(redis.exists('acls/' + self.SERVER), False)

        # Trying to set another user's ACL
        acl = AccessControlList(USERNAME2, 'block', ('bob', 'dave', 'mike'))
        acl_json = json.dumps(acl.to_dict())
        redis.set('acls/' + self.SERVER, acl_json)
        response = self.client.post('/api/acls/%s/' % self.SERVER,
                                    {'mode': 'allow',
                                     'usernames': ('bob', 'mike')},
                                    HTTP_AUTHORIZATION=self.AUTH)
        self.assertEqual(response.status_code, 403)


class UsernamesTestCase(ApiTestCase):
    def setUp(self):
        super(UsernamesTestCase, self).setUp()
        User.objects.create_user('bob1', 'bob1@example.org', PASSWORD).save()
        User.objects.create_user('bob2', 'bob2@example.org', PASSWORD).save()
        User.objects.create_user('bob3', 'bob3@example.org', PASSWORD).save()
        for i in range(1, 27):
            User.objects.create_user('Alice' + str(i),
                    'alice{}@example.org'.format(i), PASSWORD).save()

    def tearDown(self):
        User.objects.get(username__exact='bob1').delete()
        User.objects.get(username__exact='bob2').delete()
        User.objects.get(username__exact='bob3').delete()
        for i in range(1, 27):
            User.objects.get(username__exact='Alice' + str(i)).delete()
        super(UsernamesTestCase, self).tearDown()

    def test_valid_search(self):
        response = self.client.get('/api/usernames/', {'q': 'bob'},
                                   HTTP_AUTHORIZATION=self.AUTH)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data.get('usernames', []), ['bob1', 'bob2', 'bob3'])
        self.assertEqual(data.get('has_more'), False)

    def test_many_results(self):
        response = self.client.get('/api/usernames/', {'q': 'alice'},
                                   HTTP_AUTHORIZATION=self.AUTH)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data.get('usernames', []), ['Alice' + str(i) for i in range(1, 26)])
        self.assertEqual(data.get('has_more'), True)

    def test_invalid_credentials(self):
        response = self.client.get('/api/usernames/',
                                   {'q': 'Alice'},
                                   HTTP_AUTHORIZATION=self.BAD_AUTH)
        self.assertEqual(response.status_code, 401)

    def test_missing_query_argument(self):
        response = self.client.get('/api/usernames/',
                                   HTTP_AUTHORIZATION=self.AUTH)
        self.assertEqual(response.status_code, 400)

    def test_query_argument_too_short(self):
        response = self.client.get('/api/usernames/',
                                   {'q': 'a'},
                                   HTTP_AUTHORIZATION=self.AUTH)
        self.assertEqual(response.status_code, 400)
