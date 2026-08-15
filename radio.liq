#!/usr/bin/liquidsoap

# We're inside an isolated Docker container, so running as root here is fine.
settings.init.allow_root.set(true)

settings.log.stdout.set(true)
settings.log.level.set(3)

# Reads playlist.txt and automatically re-reads it if the file changes,
# so you can add/remove song links without restarting the server.
# Each line in playlist.txt should be a direct link to an .mp3 file.
radio = playlist(
  "/app/playlist.txt",
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
