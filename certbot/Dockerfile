FROM debian:bookworm-slim
RUN apt-get update && \
    apt-get install -y --no-install-recommends --no-install-suggests \
        certbot \
        cron \
        python3-docker \
        && \
    rm -rf /var/lib/apt/lists/*
RUN mkdir -p /var/www/certbot-webroot
COPY cli.ini /etc/letsencrypt/cli.ini
COPY docker-entrypoint.sh restart-web-server.py /root/
WORKDIR /root
VOLUME /etc/letsencrypt /var/www/certbot-webroot
ENTRYPOINT ["./docker-entrypoint.sh"]
