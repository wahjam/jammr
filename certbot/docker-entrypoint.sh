#!/bin/sh
set -e

extra_opts=

if test "$STAGING" = "True"
then
    extra_opts="$extra_opts --staging"
fi

certbot certonly $extra_opts --post-hook "" --non-interactive --email "$EMAIL" --agree-tos --webroot -w /var/www/certbot-webroot -d "$DOMAINS"
# TODO should we run certbot renew instead if /etc/letsencrypt files already exist?
exec cron -f
