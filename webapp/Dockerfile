FROM debian:buster-slim
RUN apt-get update && \
    apt-get install -y --no-install-recommends --no-install-suggests \
        virtualenv \
        gettext \
        && \
    rm -rf /var/lib/apt/lists/*
RUN useradd --no-log-init --create-home webapp
WORKDIR /home/webapp
ENV PATH /home/webapp/bin:$PATH
COPY pip-pkgs /tmp/pip-pkgs

RUN apt-get update && \
    apt-get install -y --no-install-recommends --no-install-suggests \
        build-essential \
        geoip-database \
        libgeoip1 \
        libpq5 \
        libpq-dev \
        libjpeg62-turbo \
        libjpeg-dev \
        zlib1g \
        zlib1g-dev \
        python3-dev && \
    /bin/su webapp -c 'virtualenv --python=python3 .' && \
    /bin/su webapp -c 'bin/pip --no-cache-dir install --no-index --find-links /tmp/pip-pkgs \
        setuptools==57.5.0' && \
    /bin/su webapp -c 'bin/pip --no-cache-dir install --no-index --find-links /tmp/pip-pkgs \
        certifi==2019.11.28 \
        chardet==3.0.4 \
        Django==1.11.26 \
        django_classy_tags==0.8.0 \
        django-cookie-law==1.0.0 \
        django-registration==2.0.4 \
        django-haystack==2.8.1 \
        django-messages==0.6.0 \
        gunicorn==18.0 \
        hiredis==1.0.1 \
        idna==2.9 \
        postmarkup==1.2.2 \
        Pillow==2.5.3 \
        psycopg2==2.7.7 \
        pygments==2.2.0 \
        pytz==2019.3 \
        redis==3.3.11 \
        requests==2.23.0 \
        schedule==0.6.0 \
        stripe==2.44.0 \
        urllib3==1.25.8 \
        Whoosh==2.7.4' && \
    apt-get purge -y --autoremove \
        build-essential \
        libpq-dev \
        libjpeg-dev \
        zlib1g-dev \
        python3-dev && \
    rm -rf /tmp/pip-pkgs /var/lib/apt/lists/*
USER webapp
COPY common /home/webapp/common
COPY djangobb_forum /home/webapp/djangobb_forum
COPY forum /home/webapp/forum
COPY pagination /home/webapp/pagination
COPY website /home/webapp/website
COPY apply_tax_rate_changes.py clear_sessions.py manage-forum.py manage-website.py docker-entrypoint.sh gunicorn-forum.conf gunicorn-stripe-webhook.conf gunicorn-website.conf send_forum_notifications.py /home/webapp/
EXPOSE 8000
ENTRYPOINT ["./docker-entrypoint.sh"]
