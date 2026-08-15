"""
Simple Radio Streaming Server
------------------------------
Streams the mp3 files inside the songs/ folder back-to-back on a loop,
like a real radio station. Everyone who connects to /stream hears the
exact same audio at the exact same moment, live — new listeners join
wherever the broadcast currently is, they don't restart from track 1.

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

BITRATE_KBPS = int(os.environ.get("BITRATE_KBPS", 128))
BYTES_PER_SECOND = (BITRATE_KBPS * 1000) // 8

# The moment the server started broadcasting. Every listener's position
# is computed relative to this, so everyone stays in sync.
BROADCAST_START = time.time()


def get_playlist():
    files = sorted(glob.glob(os.path.join(SONGS_DIR, "*.mp3")))
    if not files:
        raise RuntimeError(f"No mp3 files found in {SONGS_DIR}")
    return files


def get_playhead():
    """Figure out which song is 'currently playing' and how far into it
    we are, based on real elapsed time since the broadcast started."""
    playlist = get_playlist()
    durations = [os.path.getsize(f) / BYTES_PER_SECOND for f in playlist]
    total_duration = sum(durations)

    elapsed = (time.time() - BROADCAST_START) % total_duration

    cursor = 0.0
    for idx, dur in enumerate(durations):
        if elapsed < cursor + dur:
            return playlist, idx, elapsed - cursor
        cursor += dur
    return playlist, 0, 0.0  # fallback


def generate_stream():
    playlist, idx, offset_seconds = get_playhead()
    byte_offset = int(offset_seconds * BYTES_PER_SECOND)

    while True:  # loop forever, like a real radio station
        filepath = playlist[idx % len(playlist)]
        with open(filepath, "rb") as f:
            f.seek(byte_offset)
            while chunk := f.read(CHUNK_SIZE):
                yield chunk
                # Pace output to match real playback speed. This keeps
                # CPU usage low AND keeps every listener in sync.
                time.sleep(len(chunk) / BYTES_PER_SECOND)
        idx += 1
        byte_offset = 0  # start next song from the beginning


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
