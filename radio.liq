#!/usr/bin/liquidsoap

# We're inside an isolated Docker container, so running as root here is fine.
settings.init.allow_root.set(true)

settings.log.stdout.set(true)
settings.log.level.set(3)

# Reads local_playlist.txt (built by entrypoint.sh from your playlist.txt
# links, pre-downloaded to local files) and automatically re-reads it if
# it changes, so it stays in sync with playlist.txt on every restart.
radio = playlist(
  "/app/local_playlist.txt",
  reload_mode="watch",
  mode="normal"  # play in order, then loop back to the top forever
)

radio = mksafe(radio)

port = int_of_string(getenv("PORT"))
source_password = getenv("SOURCE_PASSWORD")

output.icecast(
  %mp3(bitrate=128),
  host="localhost",
  port=port,
  password=source_password,
  mount="/stream",
  name="Live Radio",
  radio
)
