# Copyright 2014-2022 Stefan Hajnoczi <stefanha@gmail.com>

import re
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from djangobb_forum.models import Post
from website.jammr.models import UserProfile

ip_range_re = re.compile(r'^(\d+)\.(\d+)\.(\d+)\.(\d+)\/(\d+)$')

def ip_from_dotted_quad(dotted_quad):
    a, b, c, d = (int(x) for x in dotted_quad.split('.'))
    return (a << 24) | (b << 16) | (c << 8) | d

def netmask_from_prefix(prefix):
    return (0xffffffff << (32 - int(prefix))) & 0xffffffff

def users_by_ip_range(network, netmask):
    for profile in UserProfile.objects.all():
        last_ip = ip_from_dotted_quad(profile.last_ip)
        if last_ip & netmask == network:
            yield profile.user

class Command(BaseCommand):
    help = 'Ban user accounts by username or IP range'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run',
                            action='store_true',
                            default=False,
                            help='Print results without modifying database')
        parser.add_argument('--ip-range')
        parser.add_argument('--username')

    def handle(self, *args, **options):
        if options['ip_range'] is not None:
            network, netmask = options['ip_range'].split('/')
            network = ip_from_dotted_quad(network)
            netmask = netmask_from_prefix(netmask)
            users = users_by_ip_range(network, netmask)
        elif options['username'] is not None:
            users = User.objects.filter(username=options['username'])
        else:
            self.stderr.write('expected --ip-range or --username argument')

        for u in users:
            self.stdout.write('%s %s' % (u.username, u.userprofile.last_ip))
            if not options['dry_run']:
                for p in Post.objects.filter(user=u):
                    p.delete()
                u.userprofile.soft_delete()
