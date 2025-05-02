FROM debian:buster-slim
RUN apt-get update && \
    apt-get install -y --no-install-recommends --no-install-suggests \
        virtualenv \
        libqt5network5 \
        && \
    rm -rf /var/lib/apt/lists/*
RUN useradd --no-log-init --create-home jamd
WORKDIR /home/jamd
ENV PATH /home/jamd/bin:$PATH

ARG WAHJAM_REPO=https://github.com/wahjam/wahjam
ARG WAHJAM_BRANCH=master

COPY pip-pkgs /tmp/pip-pkgs

RUN apt-get update && \
    apt-get install -y --no-install-recommends --no-install-suggests \
        build-essential \
        python3-dev && \
    /bin/su jamd -c 'virtualenv --python=python3 .' && \
    /bin/su jamd -c 'bin/pip --no-cache-dir install --no-index --find-links /tmp/pip-pkgs \
        Twisted==19.7.0 \
        txredisapi==1.4.4' && \
    apt-get install -y --no-install-recommends --no-install-suggests \
        git-core qt5-default portaudio19-dev libvorbis-dev libogg-dev libportmidi-dev && \
    cd /tmp && \
    git clone --depth=1 -b $WAHJAM_BRANCH $WAHJAM_REPO && \
    cd wahjam && \
    qmake && \
    make sub-server && \
    /bin/su jamd -c 'cp /tmp/wahjam/server/wahjamsrv /home/jamd/bin/' && \
    /bin/su jamd -c 'GIT_DIR=/tmp/wahjam/.git git describe --always --dirty >/home/jamd/wahjamsrv-version' && \
    rm -rf /tmp/wahjam && \
    apt-get purge -y --autoremove build-essential python3-dev git-core \
        qt5-default portaudio19-dev libvorbis-dev libogg-dev libportmidi-dev && \
    rm -rf /tmp/pip-pkgs /var/lib/apt/lists/*
USER jamd
COPY . /home/jamd/
EXPOSE 10100-10200
ENTRYPOINT ["./docker-entrypoint.sh"]
