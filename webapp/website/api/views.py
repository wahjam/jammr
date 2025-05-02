# Copyright 2012-2020 Stefan Hajnoczi <stefanha@gmail.com>

import json
import uuid
import logging
from redis.exceptions import RedisError
from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse, \
                        HttpResponseNotFound, HttpResponseForbidden, \
                        HttpResponseBadRequest, HttpResponseServerError
from website.utils import redis, render_json, http_basic_auth, RestApiView
from . import models

logger = logging.getLogger('website.api')

class TokenView(RestApiView):
    '''Authentication token for jam servers'''
    http_method_names = ['get', 'post']
    EXPIRE_SECS = 6 * 60 * 60

    @http_basic_auth()
    def get(self, request, username):
        def is_owner():
            '''Does the user own the server?'''
            if 'server' not in request.GET:
                return False

            server = request.GET['server']
            acl_json = redis.get('acls/%s' % server)
            if acl_json is None:
                return False

            try:
                data = json.loads(acl_json)
            except ValueError:
                logger.exception('Failed to parse ACL JSON: %s', acl_json)
                return False

            try:
                acl = models.AccessControlList.from_dict(data)
            except ValueError:
                logger.exception('Failed to create ACL from dict: %s', acl_json)
                return False

            return acl.is_owner(username)

        if not request.user.has_perm('auth.can_read_token'):
            return HttpResponseForbidden('Forbidden')

        token = redis.get('tokens/%s' % username)
        if token is None:
            return HttpResponseNotFound('Not Found')

        privs = 'cv' # PRIV_CHATSEND | PRIV_VOTE
        if is_owner():
            # PRIV_TOPIC | PRIV_BPM | PRIV_KICK | PRIV_RESERVE
            privs += 'tbkr'

        return render_json({'token': token, 'privs': privs})

    @http_basic_auth()
    def post(self, request, username):
        if request.user.username != username:
            # Refuse email address as login because client would then continue
            # to use the email instead of username in further APIs that expect
            # the username.  This restriction can be fixed later.
            if request.user.email == username:
                response = HttpResponse('Not Authorized', status=401)
                response['WWW-Authenticate'] = 'Basic realm="api"'
                return response
            return HttpResponseForbidden('Forbidden')

        if 'token' not in request.POST:
            return HttpResponseBadRequest('Bad Request')
        val = request.POST['token']
        if len(val) != 40:
            return HttpResponseBadRequest('Bad Request')
        try:
            bytes.fromhex(val)
        except:
            return HttpResponseBadRequest('Bad Request')

        key = 'tokens/%s' % username
        redis.pipeline() \
             .set(key, val) \
             .expire(key, TokenView.EXPIRE_SECS) \
             .execute()
        return HttpResponse('Created', status=201)

class LivejamView(RestApiView):
    '''Live jam servers'''
    http_method_names = ['get', 'post']

    @http_basic_auth()
    def get(self, request):
        visible_private_jams = set()
        if request.user.has_perm('auth.can_join_private_jams'):
            acl_keys = redis.keys('acls/*')
            if acl_keys:
                acl_values = redis.mget(acl_keys)
            else:
                acl_values = () # MGET needs at least one key

            for acl_key, acl_json in zip(acl_keys, acl_values):
                # Key was deleted between KEYS and MGET calls
                if acl_json is None:
                    continue

                try:
                    data = json.loads(acl_json)
                except ValueError:
                    logger.exception('Failed to parse ACL JSON: %s', acl_json)
                    continue

                try:
                    acl = models.AccessControlList.from_dict(data)
                except ValueError:
                    logger.exception('Failed to create ACL from dict: %s', acl_json)
                    continue

                if acl.is_allowed(request.user.username):
                    visible_private_jams.add(acl_key[len("acls/"):])

        result = []
        for jam_json in redis.mget_keys('livejams/*'):
            try:
                data = json.loads(jam_json)
            except ValueError:
                logger.exception('Failed to parse livejam: %s', jam_json)
                continue

            # Skip private jams that block this user
            if not data.get('is_public', True):
                if data.get('server', None) not in visible_private_jams:
                    continue

            result.append(data)

        return render_json(result)

    @http_basic_auth()
    def post(self, request):
        if not request.user.has_perm('auth.can_create_private_jams'):
            return HttpResponse('Not Authorized', status=401)

        topic = request.POST.get('topic', '%s\'s jam' % request.user.username)
        acl_json = json.dumps(models.AccessControlList(request.user.username, 'allow').to_dict())
        response_id = uuid.uuid4().hex

        try:
            redis.rpush('create_jam', json.dumps(dict(topic=topic, response_id=response_id, acl=acl_json, owner=request.user.username)))
            result = redis.blpop(['create_jam_responses/' + response_id], timeout=settings.REDIS_TIMEOUT)
        except RedisError:
            logger.exception('Failed to create a private jam')
            return HttpResponseServerError('Internal Server Error')
        if result is None:
            logger.error('Timeout expired while waiting for private jam creation')
            return HttpResponseServerError('Internal Server Error')
        try:
            result = json.loads(result[1])
        except ValueError:
            logger.exception('Failed to parse create jam response JSON: %s', result)
            return HttpResponseServerError('Internal Server Error')
        if 'server' not in result:
            logger.error('Missing "server" field in create jam response: %s', result)
            return HttpResponseServerError('Internal Server Error')
        logger.info('Created private jam at "%s" for user "%s"', result['server'], request.user.username)
        return render_json({'server': result['server']})

class ACLView(RestApiView):
    '''Access control lists'''
    http_method_names = ['get', 'post']

    @http_basic_auth()
    def get(self, request, server):
        try:
            acl_json = redis.get('acls/%s' % server)
        except RedisError:
            logger.exception('Failed to get ACL')
            return HttpResponseServerError('Internal Server Error')
        if acl_json is None:
            return HttpResponseNotFound('Not Found')

        try:
            data = json.loads(acl_json)
        except ValueError:
            logger.exception('Failed to parse ACL JSON: %s', acl_json)
            return HttpResponseServerError('Internal Server Error')

        try:
            acl = models.AccessControlList.from_dict(data)
        except ValueError:
            logger.exception('Failed to create ACL from dict: %s', acl_json)
            return HttpResponseServerError('Internal Server Error')

        if not acl.is_owner(request.user.username):
            return HttpResponseForbidden('Forbidden')

        return render_json(data)

    @http_basic_auth()
    def post(self, request, server):
        # Fetch the existing ACL and check user owns it
        try:
            acl_json = redis.get('acls/%s' % server)
        except RedisError:
            logger.exception('Failed to get ACL')
            return HttpResponseServerError('Internal Server Error')
        if acl_json is None:
            # Cannot create new ACLs only overwrite existing ones
            return HttpResponseForbidden('Forbidden')

        try:
            data = json.loads(acl_json)
        except ValueError:
            logger.exception('Failed to parse ACL JSON: %s', acl_json)
            return HttpResponseServerError('Internal Server Error')

        try:
            acl = models.AccessControlList.from_dict(data)
        except ValueError:
            logger.exception('Failed to create ACL from dict: %s', acl_json)
            return HttpResponseServerError('Internal Server Error')

        if not acl.is_owner(request.user.username):
            return HttpResponseForbidden('Forbidden')

        # Update the ACL with the user's mode and usernames
        if 'mode' not in request.POST:
            return HttpResponseBadRequest('Bad Request')

        data['mode'] = request.POST['mode']
        data['usernames'] = request.POST.getlist('usernames')

        try:
            acl = models.AccessControlList.from_dict(data)
        except ValueError:
            return HttpResponseBadRequest('Bad Request')

        acl_json = json.dumps(acl.to_dict())

        try:
            redis.set('acls/%s' % server, acl_json)
        except RedisError:
            logger.exception('Failed to update ACL')
            return HttpResponseServerError('Internal Server Error')

        return HttpResponse('Created', status=201)


class UsernamesView(RestApiView):
    '''Username search view'''
    http_method_names = ['get']

    @http_basic_auth()
    def get(self, request):
        q = request.GET.get('q')
        if q is None or len(q) < 3:
            return HttpResponseBadRequest('Bad Request')

        usernames = [u.username for u in User.objects.filter(username__istartswith=q).all()[:26]]
        has_more = len(usernames) == 26
        usernames = usernames[:25]

        return render_json({
            'usernames': usernames,
            'has_more': has_more,
        })
