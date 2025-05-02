# Copyright 2018 Stefan Hajnoczi <stefanha@gmail.com>

from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives, get_connection

class Command(BaseCommand):
    help = 'Send a templated email to one or more users'

    def add_arguments(self, parser):
        parser.add_argument('template')
        parser.add_argument('users', nargs='+')

    def handle(self, *args, **options):
        template = options['template']

        if '/' in template:
            raise CommandError('Template base name cannot contain "/"')

        messages = []

        for username in options['users']:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise CommandError('User "%s" does not exist' % username)

            context_dict = {
                'user': user
            }

            subject = render_to_string('emails/%s_subject.txt' % template, context_dict).rstrip()
            text_content = render_to_string('emails/%s_content.txt' % template, context_dict)
            html_content = render_to_string('emails/%s_content.html' % template, context_dict)

            msg = EmailMultiAlternatives(subject,
                                         text_content,
                                         None,
                                         [user.email])
            msg.attach_alternative(html_content, 'text/html')
            messages.append(msg)

        get_connection().send_messages(messages)
