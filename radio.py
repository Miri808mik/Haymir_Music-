"""
Simple Radio Streaming Server
------------------------------
Streams a folder of mp3 files back-to-back on a loop, like a basic radio
station. Point any audio player (browser, VLC, phone) at the /stream URL
and it will keep playing songs one after another, forever.

Deploy this on Render as a "Web Service":
    - Build command: pip install -r requirements.txt
    - Start command: python radio.py
"""

import os
import glob
from flask import Flask, Response

app = Flask(__name__)

SONGS_DIR = os.path.join(os.path.dirname(__file__), "songs")
CHUNK_SIZE = 4096


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
        i += 1


@app.route("/stream")
def stream():
    return Response(generate_stream(), mimetype="audio/mpeg")


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
