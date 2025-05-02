from datetime import timedelta

from django.core.cache import cache
from django.utils import translation, timezone
from django.conf import settings as global_settings
import pytz

from djangobb_forum import settings as forum_settings

class LastLoginMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated():
            cache.set('djangobb_user%d' % request.user.id, True, forum_settings.USER_ONLINE_TIMEOUT)
        return self.get_response(request)

class ForumMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated():
            profile = request.user.forum_profile
            language = translation.get_language_from_request(request)

            if not profile.language:
                profile.language = language
                profile.save()

            if profile.language and profile.language != language:
                request.session['django_language'] = profile.language
                translation.activate(profile.language)
                request.LANGUAGE_CODE = translation.get_language()
        return self.get_response(request)

class UsersOnline(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        now = timezone.now()
        delta = now - timedelta(seconds=forum_settings.USER_ONLINE_TIMEOUT)
        users_online = cache.get('djangobb_users_online', {})
        guests_online = cache.get('djangobb_guests_online', {})

        if request.user.is_authenticated():
            users_online[request.user.id] = now
        else:
            guest_sid = request.COOKIES.get(global_settings.SESSION_COOKIE_NAME, '')
            guests_online[guest_sid] = now

        for user_id in list(users_online.keys()):
            if users_online[user_id] < delta:
                del users_online[user_id]

        for guest_id in list(guests_online.keys()):
            if guests_online[guest_id] < delta:
                del guests_online[guest_id]

        cache.set('djangobb_users_online', users_online, 60*60*24)
        cache.set('djangobb_guests_online', guests_online, 60*60*24)
        return self.get_response(request)


class TimezoneMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated():
            profile = request.user.forum_profile
            try:
                timezone.activate(profile.time_zone)
            except pytz.UnknownTimeZoneError:
                profile.time_zone = global_settings.TIME_ZONE
                profile.save()
        return self.get_response(request)
