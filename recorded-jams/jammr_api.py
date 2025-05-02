# Copyright (C) 2013-2020 Stefan Hajnoczi <stefanha@gmail.com>

import ssl
import http.client
import urllib.request, urllib.parse, urllib.error
import logging
import settings
import base64

__all__ = ['add_recorded_jam']
log = logging.getLogger(__name__)

ISO8601_DATETIME_FMT = '%Y-%m-%dT%H:%MZ'
ISO8601_TIME_FMT = '%H:%M:%S'

def jammr_api_call(url, post_data=None):
    '''Make a REST API call and return (status_code, response_body)'''
    data = None
    if post_data is not None:
        data = urllib.parse.urlencode(post_data, 1).encode('utf-8')

    auth = 'Basic ' + base64.b64encode(settings.jammr_user.encode('utf-8') + b':' + settings.jammr_password.encode('utf-8')).decode('utf-8').strip()

    req = urllib.request.Request(settings.jammr_api_url + url, data, {'Authorization': auth})

    ctx = ssl.create_default_context()
    if not settings.ssl_verify:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    try:
        resp = urllib.request.urlopen(req, context=ctx)
    except urllib.error.URLError:
        log.exception('REST API request failed')
        raise

    return resp.getcode(), resp.read().decode('utf-8')

def can_access_recorded_jams(users):
    query = ''
    if users:
        query = '?' + '&'.join('u=' + urllib.parse.quote_plus(username) for username in users)

    resp_code, resp_body = jammr_api_call('can-access-recorded-jams/' + query)
    if resp_code != http.client.OK:
        msg = 'Unexpected HTTP status code {}'.format(resp_code)
        log.error(msg)
        raise RuntimeError(msg)

    return resp_body.lower() == 'true'

def add_recorded_jam(start_date, users, owner, mix_url, tracks_url, duration, server):
    data = {
        'start_date': start_date.strftime(ISO8601_DATETIME_FMT),
        'users': list(users),
        'mix_url': mix_url,
        'tracks_url': tracks_url,
        'duration': duration.strftime(ISO8601_TIME_FMT),
        'server': server,
    }
    if owner:
        data['owner'] = owner

    resp_code, _ = jammr_api_call('recorded-jams/', data)
    if resp_code != http.client.CREATED:
        msg = 'Unexpected HTTP status code %s' % resp_code
        log.error(msg)
        raise RuntimeError(msg)
