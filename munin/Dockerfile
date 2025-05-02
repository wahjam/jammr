FROM debian:stretch-slim
RUN apt-get update && \
    apt-get install -y --no-install-recommends --no-install-suggests \
        munin \
        libcgi-fast-perl \
        spawn-fcgi \
        && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /var/run/munin && chown munin /var/run/munin
COPY munin.conf /etc/munin/munin.conf
COPY docker-entrypoint.sh /
VOLUME ["/etc/munin/munin-conf.d"]
ENTRYPOINT ["/docker-entrypoint.sh"]
