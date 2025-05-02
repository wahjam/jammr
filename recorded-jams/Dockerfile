# The build image for cliplogcvt
FROM debian:buster-slim AS recorded-jams-build
RUN apt-get update && \
    apt-get install -y --no-install-recommends --no-install-suggests \
        build-essential git-core qt5-default libvorbis-dev libogg-dev libresample1-dev \
	python3-dev pkg-config ca-certificates libbz2-dev liblzma-dev \
        libmp3lame-dev libopus-dev librubberband-dev libsnappy-dev libsoxr-dev \
	libtwolame-dev libvpx-dev libx264-dev libx265-dev libxml2-dev nasm \
        zlib1g-dev wget && \
    cd /var/tmp && \
    git clone --depth=1 https://github.com/wahjam/wahjam && \
    cd wahjam && \
    qmake && \
    make sub-cliplogcvt && \
    git describe --always --dirty >cliplogcvt-version && \
    cd /var/tmp && \
    wget https://ffmpeg.org/releases/ffmpeg-4.4.tar.xz && \
    tar xf ffmpeg-4.4.tar.xz && \
    cd ffmpeg-4.4 && \
    ./configure --prefix=/usr --enable-gpl --enable-version3 --enable-nonfree --disable-ffplay --disable-doc && \
    make -j$(nproc) && \
    mkdir installroot && \
    make DESTDIR=installroot install

# The recorded-jams image
FROM debian:buster-slim
RUN apt-get update && \
    apt-get install -y --no-install-recommends --no-install-suggests \
        virtualenv \
        libqt5core5a libvorbis0a libvorbisenc2 libvorbisfile3 libogg0 libresample1 \
        libxcb-xfixes0 libxcb-shape0 \
        && \
    rm -rf /var/lib/apt/lists/*
RUN useradd --no-log-init --create-home recorded_jams
WORKDIR /home/recorded_jams
USER recorded_jams
ENV PATH /home/recorded_jams/bin:$PATH
COPY --from=recorded-jams-build --chown=recorded_jams:recorded_jams /var/tmp/wahjam/cliplogcvt/cliplogcvt /home/recorded_jams/bin/
COPY --from=recorded-jams-build --chown=recorded_jams:recorded_jams /var/tmp/wahjam/cliplogcvt-version /home/recorded_jams/
COPY --from=recorded-jams-build /var/tmp/ffmpeg-4.4/installroot/usr/bin/ffmpeg /usr/bin/
COPY --from=recorded-jams-build /var/tmp/ffmpeg-4.4/installroot/usr/bin/ffprobe /usr/bin/
COPY --chown=recorded_jams:recorded_jams pip-pkgs /tmp/pip-pkgs
RUN virtualenv --python=python3 . && \
    bin/pip --no-cache-dir install --no-index --find-links /tmp/pip-pkgs \
        Twisted==19.7.0 \
        boto==2.49.0 && \
    rm -rf /tmp/pip-pkgs
COPY . /home/recorded_jams/
ENTRYPOINT ["./docker-entrypoint.sh"]
