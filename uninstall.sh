#!/bin/bash
set -e

rm ~/.local/share/kservices5/plasma-runner-spotify.desktop
rm ~/.local/share/dbus-1/services/org.kde.runner-spotify.service
kquitapp5 krunner
