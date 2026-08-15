FROM debian:bookworm-slim

# Icecast = the actual radio broadcast server (this is what Highrise needs)
# Liquidsoap = reads your playlist.txt and feeds songs into Icecast, forever
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        icecast2 \
        liquidsoap \
        gettext-base \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Dedicated user for icecast2 to drop root privileges into (icecast2
# refuses to run as root for security reasons)
RUN groupadd -f icecastgrp && \
    useradd -r -g icecastgrp -M -s /usr/sbin/nologin icecastusr && \
    mkdir -p /var/log/icecast2 && \
    chown -R icecastusr:icecastgrp /var/log/icecast2 /usr/share/icecast2 /etc/icecast2

WORKDIR /app

COPY icecast.xml.template /app/icecast.xml.template
COPY radio.liq /app/radio.liq
COPY playlist.txt /app/playlist.txt
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Render assigns the real port at runtime via $PORT
ENV PORT=8000
ENV SOURCE_PASSWORD=changeme123

EXPOSE 8000

CMD ["/app/entrypoint.sh"]
