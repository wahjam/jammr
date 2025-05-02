# Copyright 2015-2020 Stefan Hajnoczi <stefanha@gmail.com>

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from djangobb_forum.models import Forum, Topic, Post

class Command(BaseCommand):
    help = 'Add a new topic to a forum'

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('forum_id')
        parser.add_argument('subject')
        parser.add_argument('filename')

    def handle(self, *args, **options):
        username = options['username']
        forum_id = options['forum_id']
        name = options['subject']
        filename = options['filename']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError('User "%s" does not exist' % username)

        try:
            forum = Forum.objects.get(pk=int(forum_id))
        except:
            raise CommandError('Forum %s does not exist' % forum_id)

        body = open(filename, 'rb').read().decode('utf-8')

        topic =Topic(forum=forum, user=user, name=name)
        topic.save()

        post = Post(topic=topic, user=user, body=body)
        post.save()
