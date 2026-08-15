#!/bin/bash
set -e

echo "Starting Icecast on port $PORT ..."

# Fill in $PORT and $SOURCE_PASSWORD into the icecast config
envsubst '${PORT} ${SOURCE_PASSWORD}' < /app/icecast.xml.template > /etc/icecast2/icecast.xml

# Start Icecast in the background
icecast2 -c /etc/icecast2/icecast.xml -b

# Give Icecast a moment to be ready to accept a source connection
sleep 3

echo "Starting Liquidsoap (this feeds your playlist into Icecast) ..."
exec liquidsoap /app/radio.liq
