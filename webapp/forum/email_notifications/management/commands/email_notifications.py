# Copyright 2013-2020 Stefan Hajnoczi <stefanha@gmail.com>

import datetime
from django.contrib.sites.shortcuts import get_current_site
from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail
from django.template.loader import render_to_string
from djangobb_forum import models

class Command(BaseCommand):
    help = 'Send email notifications about new forum posts'

    def handle(self, *args, **options):
        topics = {}
        yesterday = datetime.date.today() - datetime.timedelta(1)
        for p in models.Post.objects.filter(created__gte=yesterday):
            if p.topic.id in topics:
                topics[p.topic.id][1].add(p.user.username)
            else:
                topics[p.topic.id] = (p, set((p.user.username,)))

        if not topics:
            return

        context_dict = {
            'topics': topics.values(),
            'site': get_current_site(None),
        }
        subject = render_to_string('email_notifications/email_post_subject.txt', context_dict).rstrip()
        message = render_to_string('email_notifications/email_post_content.txt', context_dict)
        send_mail(subject, message, 'info@jammr.net', ['stefanha@jammr.net', 'andhai@jammr.net'])
