### UTILI COMANDI

- per docker desktop
  - docker compose up -d --build
  - gremlin attach check-power-app-1

- avviare con:
  - docker build -t check-power .
  - docker run -d --restart=always --name check-power-app-2 -e HA_MEDIA_PLAYER_ID="media_player.mopidy" -e HA_TTS_SERVICE_TOPIC="ha/tts/picotts_say" check-power

- notes:
  - la configurazione delle versioni dei requirements è critica

### MOPIDY 
IP: 192.168.147.2 (nb: static ip)

### MOPIDY AUDIO TEST
docker run --name mopidy-audiotest \
    --user root --device /dev/snd \
    wernight/mopidy \
    gst-launch-1.0 audiotestsrc ! audioresample ! autoaudiosink

### MOPIDY RUN
docker run -d --name mopidy \
    --user root --device /dev/snd \
    -v "$PWD/media:/var/lib/mopidy/media:ro" \
    -v "$PWD/local:/var/lib/mopidy/local" \
    -v "$PWD/playlists:/var/lib/mopidy/playlists" \
    -p 6600:6600 -p 6680:6680 \
    --user $UID:$GID \
    wernight/mopidy \
    mopidy \
    -o spotify/enabled=false \
    -o gmusic/enabled=false \
    -o soundcloud/enabled=false