#!/bin/bash
set -ex
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
if [[ -z "$XDG_DATA_HOME" ]]; then
    prefix=~/.local/share
else
    prefix="$XDG_DATA_HOME"
fi

mkdir -p "$prefix/kservices5/krunner/dbusplugins/"
mkdir -p "$prefix/dbus-1/services/"

cp "${DIR}/plasma-runner-spotify.desktop" "$prefix/kservices5/krunner/dbusplugins/"
sed "s|%{PROJECTDIR}/runner_spotify.py|${PWD}/runner_spotify.py|" "org.kde.runner_spotify.service" > "$prefix/dbus-1/services/org.kde.runner_spotify.service"

ps -ef | grep 'runner_spotify.py$' | awk '{print $2}' | xargs kill || true
kquitapp5 krunner
