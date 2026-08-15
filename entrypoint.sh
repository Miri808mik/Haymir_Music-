#!/bin/bash
set -e

echo "Starting Icecast on port $PORT ..."

# Fill in $PORT and $SOURCE_PASSWORD into the icecast config
envsubst '${PORT} ${SOURCE_PASSWORD}' < /app/icecast.xml.template > /etc/icecast2/icecast.xml

# Start Icecast in the background
icecast2 -c /etc/icecast2/icecast.xml -b

# Give Icecast a moment to be ready to accept a source connection
sleep 3

# --- Download every link in playlist.txt as a real local file first ---
# Some sites (common with Iranian music hosts) don't return a proper
# Content-Type header, which makes Liquidsoap fail to detect the file
# as audio when streamed directly ("Failed to fetch mime-type"). Curl,
# with a normal browser User-Agent, downloads the actual bytes fine
# regardless of that header. Once it's a local file, Liquidsoap detects
# the format from the .mp3 extension instead, no mime-type needed.
echo "Downloading songs from playlist.txt ..."
mkdir -p /app/songs
> /app/local_playlist.txt

while IFS= read -r url; do
    url="$(echo "$url" | xargs)"  # trim whitespace
    [[ -z "$url" || "$url" == \#* ]] && continue

    filename="$(basename "$url" | sed 's/%20/_/g; s/[^A-Za-z0-9._-]/_/g')"
    outpath="/app/songs/$filename"

    if [ ! -s "$outpath" ]; then
        echo "  Downloading: $url"
        curl -sL --max-time 60 \
             -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36" \
             -o "$outpath" "$url" || true
    fi

    # Verify it's actually audio and not an error page / empty file
    if [ -s "$outpath" ] && file --mime-type -b "$outpath" | grep -q "^audio/"; then
        echo "$outpath" >> /app/local_playlist.txt
        echo "  OK: $filename"
    else
        echo "  FAILED (not a valid audio file, skipping): $url"
        rm -f "$outpath"
    fi
done < /app/playlist.txt

echo "Download step finished. Songs ready to broadcast:"
cat /app/local_playlist.txt || echo "  (none — check the links in playlist.txt)"

echo "Starting Liquidsoap (this feeds your playlist into Icecast) ..."
exec liquidsoap /app/radio.liq
