FROM debian:bookworm-slim
RUN apt-get update && \
    apt-get install -y --no-install-recommends --no-install-suggests \
        exim4 \
        && \
    rm -rf /var/lib/apt/lists/*
ADD --chown=root:Debian-exim dkim.private.key /etc/exim4/
ADD exim4.conf.localmacros /etc/exim4/
ADD update-exim4.conf.conf /etc/exim4/
RUN update-exim4.conf
EXPOSE 25
ENTRYPOINT ["/usr/sbin/exim4"]
CMD ["-bdf", "-v", "-q30m"]
