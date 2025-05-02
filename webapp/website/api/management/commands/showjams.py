# Copyright 2013-2019 Stefan Hajnoczi <stefanha@gmail.com>

from django.core.management.base import BaseCommand, CommandError
from website.utils import redis
from website.api.models import AccessControlList
import json

class Command(BaseCommand):
    help = 'Print active jams'

    def handle(self, *args, **options):
        public_jams = 0
        private_jams = 0
        users = set()

        first = True
        for jam_json in redis.mget_keys('livejams/*'):
            if first:
                first = False
            else:
                self.stdout.write('\n')

            data = json.loads(jam_json)

            if data['is_public']:
                public_jams += 1
            else:
                private_jams += 1
            users.update(data['users'])

            self.stdout.write('server: %s\n' % data['server'])
            self.stdout.write('topic: %s\n' % data['topic'])
            self.stdout.write('slots: %s/%s\n' % (data['numusers'], data['maxusers']))
            self.stdout.write('tempo: %s BPM/%s BPI\n' % (data['bpm'], data['bpi']))
            self.stdout.write('is_public: %s\n' % data['is_public'])
            self.stdout.write('users: %s\n' % ', '.join(data['users']))

            acl_json = redis.get('acls/%s' % data['server'])
            if acl_json is None:
                continue

            data = json.loads(acl_json)
            acl = AccessControlList.from_dict(data)

            self.stdout.write('acl.owner: %s\n' % acl.owner)
            self.stdout.write('acl.mode: %s\n' % acl.mode)
            self.stdout.write('acl.usernames: %s\n' % ', '.join(acl.usernames))

        if not first:
            self.stdout.write('\n')

        self.stdout.write('%d public, %d private, %d users online\n' % (public_jams, private_jams, len(users)))
