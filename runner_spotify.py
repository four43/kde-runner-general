#!/usr/bin/python3

import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from time import sleep
import logging
import os
import subprocess
from rapidfuzz import fuzz, process

DIR = os.path.dirname(os.path.realpath(__file__))

logger = logging.getLogger(__name__)
logging.basicConfig(filename=f"{DIR}/ouput.log", encoding="utf-8", level=logging.DEBUG)


DBusGMainLoop(set_as_default=True)

objpath = "/runner_spotify"

iface = "org.kde.krunner1"

commands = {
    "lofi": {
        "action": "play playlist:74sUjcvpGfdOvCHvgzNEDO",
        "desc": "Play Lofi Hip Hop Beats on Spotify",
        "icon": "media-playback-start",
        "meta": {"subtext": "musi to study/relax to"},
    },
    "pause": {
        "action": "pause",
        "desc": "Pause Spotify Playback",
        "icon": "media-playback-pause",
        "meta": {},
    }
}


class SpotifyDbusClient:

    dbus_dest: str = "org.mpris.MediaPlayer2.spotify"
    dbus_path: str = "/org/mpris/MediaPlayer2"
    dbus_memb: str = "org.mpris.MediaPlayer2.Player"
    dbus_prop_memb: str = "org.freedesktop.DBus.Properties"

    def __init__(self):
        session_bus = dbus.SessionBus()
        spotify = session_bus.get_object(
            SpotifyDbusClient.dbus_dest, SpotifyDbusClient.dbus_path
        )
        self.cmd_iface = dbus.Interface(
            spotify, dbus_interface=SpotifyDbusClient.dbus_memb
        )

        self.property_iface = dbus.Interface(
            spotify, dbus_interface=SpotifyDbusClient.dbus_prop_memb
        )

    def get_property(self, key: str):
        return self.property_iface.Get(SpotifyDbusClient.dbus_memb, key)

    @property
    def is_playing(self):
        return self.get_property("PlaybackStatus") == "Playing"

    def pause(self):
        return self.cmd_iface.Pause()

    def play_uri(self, uri: str):
        self.cmd_iface.OpenUri(f"spotify:{uri}")


class Runner(dbus.service.Object):
    def __init__(self):
        dbus.service.Object.__init__(
            self,
            dbus.service.BusName("org.kde.runner_spotify", dbus.SessionBus()),
            objpath,
        )

        self.spotify_client = SpotifyDbusClient()

    @dbus.service.method(iface, in_signature="s", out_signature="a(sssida{sv})")
    def Match(self, query: str):
        """This method is used to get the matches and it returns a list of tupels"""

        logger.info(f"Matching {query}")

        results = process.extract(
            query, list(commands.keys()), scorer=fuzz.token_sort_ratio, score_cutoff=70
        )
        logger.info(f"Search results: {results}")

        output = []
        for result_key, score, _ in results:
            command = commands[result_key]
            output.append((
                command["action"],
                command["desc"],
                command["icon"],
                100,
                score/100,
                command["meta"]
            ))
        return output

    @dbus.service.method(iface, out_signature="a(sss)")
    def Actions(self):
        # id, text, icon
        return [("id", "Spotify Runner", "com.spotify.Client")]

    @dbus.service.method(iface, in_signature="ss")
    def Run(self, data: str, action_id: str):
        try:
            logger.info(f"Run: {data} | {action_id}")
            command_parts = data.split(" ")
            command = command_parts[0]
            command_args = command_parts[1:]

            if command == "play-pause":
                logger.info(f"\tplay-pause: {command_args[0]}")
                self.spotify_client.play_uri(command_args[0])
        except Exception as err:
            logger.exception(err)


runner = Runner()
loop = GLib.MainLoop()
loop.run()
