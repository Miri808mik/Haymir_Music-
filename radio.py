"""
Simple Radio Streaming Server
------------------------------
Streams the mp3 files inside the songs/ folder back-to-back on a loop,
like a real radio station. Everyone who connects to /stream hears the
exact same audio at the exact same moment, live.

Deploy this on Render as a "Web Service":
    - Build command: pip install -r requirements.txt
    - Start command: gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 16 --timeout 120 radio:app
"""

import os
import glob
import time
from flask import Flask, Response

app = Flask(__name__)

SONGS_DIR = os.path.join(os.path.dirname(__file__), "songs")
CHUNK_SIZE = 4096

# Target bitrate used to pace the stream at real playback speed.
# 128 kbps is a standard mp3 bitrate. If your files use a different
# bitrate, adjust this (or set the BITRATE_KBPS env var) for accurate pacing.
BITRATE_KBPS = int(os.environ.get("BITRATE_KBPS", 128))
BYTES_PER_SECOND = (BITRATE_KBPS * 1000) // 8


def get_playlist():
    files = sorted(glob.glob(os.path.join(SONGS_DIR, "*.mp3")))
    if not files:
        raise RuntimeError(f"No mp3 files found in {SONGS_DIR}")
    return files


def generate_stream():
    playlist = get_playlist()
    i = 0
    while True:  # loop forever, like a real radio station
        filepath = playlist[i % len(playlist)]
        with open(filepath, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                yield chunk
                # Pace output to match real playback speed instead of
                # dumping the whole file instantly. This keeps CPU usage
                # low (won't lock up the free-tier instance) and is also
                # what makes every listener hear the same moment together.
                time.sleep(len(chunk) / BYTES_PER_SECOND)
        i += 1


@app.route("/stream")
def stream():
    response = Response(generate_stream(), mimetype="audio/mpeg")
    response.headers["Cache-Control"] = "no-cache, no-store"
    response.headers["X-Accel-Buffering"] = "no"
    response.headers["Connection"] = "keep-alive"
    return response


@app.route("/")
def home():
    songs = [os.path.basename(f) for f in get_playlist()]
    return {
        "status": "radio is running",
        "stream_url": "/stream",
        "playlist": songs,
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    app.run(host="0.0.0.0", port=port, threaded=True)
