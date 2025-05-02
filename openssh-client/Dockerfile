FROM debian:buster-slim
RUN apt-get update && \
    apt-get install -y --no-install-recommends --no-install-suggests \
        openssh-client \
        && \
    rm -rf /var/lib/apt/lists/*
RUN useradd --no-log-init --create-home user
WORKDIR /home/user
USER user
RUN mkdir --mode=0700 .ssh
ENTRYPOINT ["/usr/bin/ssh"]
