#!/bin/bash
set -e
usage="$0 Spotify Runner Helper

Controlls spotify via DBUS, conforming to krunner_shell spec.

Actions:
  list - List available commands for consumption by krunner
"

action="$1"
shift
if [[ -z "$action" ]] || [[ "$action" == "-h" ]] || [[ "$action" == "--help" ]]; then
    echo "$usage" >&2
    exit 0
fi

function list() {
    echo -e "lofi\tplay playlist:74sUjcvpGfdOvCHvgzNEDO\tPlay Lofi Hip Hop Beats on Spotify\tmedia-playback-start\tmusic to study/relax to"
    echo -e "pause\tpause\tPause Spotify playback\tmedia-playback-pause"
    echo "META-CACHE=60"
}

function play() {
    dbus-send \
    --type=method_call \
    --dest=org.mpris.MediaPlayer2.spotify \
    /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.OpenUri \
    "string:spotify:$1"
}

case "$action" in
    "list")
        list
        ;;
    "play")
        play $@
        ;;
esac