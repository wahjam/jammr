#!/bin/bash
set -e

PROJECT=$1
if [ -z "$PROJECT" ]; then
    echo "$0: missing <project> argument" >&2
    exit 1
fi

if [ "$PROJECT" = "announce_weekly_jam" ]; then
    exec ./announce_weekly_jam.py
fi

if [ "$PROJECT" = "clear_sessions" ]; then
    exec ./clear_sessions.py
fi

if [ "$PROJECT" = "send_forum_notifications" ]; then
    exec ./send_forum_notifications.py
fi

if [ "$PROJECT" = "apply_tax_rate_changes" ]; then
    exec ./apply_tax_rate_changes.py
fi

# The stripe webhook is just the website with a special gunicorn.conf
if [ "$PROJECT" = "stripe-webhook" ]; then
    exec gunicorn --config gunicorn-stripe-webhook.conf website.wsgi:application
fi

./manage-$PROJECT.py collectstatic --noinput --clear
./manage-website.py migrate --noinput --fake-initial
exec gunicorn --config gunicorn-$PROJECT.conf $PROJECT.wsgi:application
