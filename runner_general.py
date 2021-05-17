#!/usr/bin/python3

import logging
import subprocess
from pathlib import Path
from typing import List, Optional

import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from rapidfuzz import fuzz, process

from dataclasses import dataclass

DIR = Path(__file__).parent

logger = logging.getLogger(__name__)

DBusGMainLoop(set_as_default=True)

objpath = "/runner_general"

iface = "org.kde.krunner1"


@dataclass
class Action:
    namespace: str
    key: str
    command: str
    description: str
    icon: Optional[str]
    subtext: Optional[str]

    def to_dbus_tuple(self, score: int):
        return (
            self.command,
            self.description,
            self.icon,
            100,
            score / 100,
            {"subtext": self.subtext} if self.subtext is not None else {},
        )


class RunnersManager:
    def __init__(self, runners_dir: str = DIR / "runners.d"):
        self.runners_dir = runners_dir

    def actions(self) -> List[Action]:
        """
        Run each runner asking for their possible actions
        """
        actions = []
        for runner_path in self._get_runners():
            runner_path_str: str = str(runner_path.absolute())
            output = subprocess.run([runner_path_str, "actions"], capture_output=True)
            for action in output.stdout.decode("utf-8").splitlines():
                if action.startswith("META-"):
                    # @todo Add meta caching
                    continue
                actions.append(RunnersManager._parse_action(runner_path_str, action))
        return actions

    def get_action_by_key(self, key: str) -> Optional[Action]:
        for action in self.actions():
            if action.key == key:
                return action

    def _get_runners(self) -> List[Path]:
        return self.runners_dir.glob("**/*")

    @staticmethod
    def _parse_action(namespace: str, action: str) -> Action:
        action_parts = action.split("\t")
        return Action(
            namespace=namespace,
            key=action_parts[0],
            command=action_parts[1],
            description=action_parts[2] if len(action_parts) > 2 else None,
            icon=action_parts[3] if len(action_parts) > 3 else None,
            subtext=action_parts[4] if len(action_parts) > 4 else None,
        )


class DbusRunner(dbus.service.Object):
    def __init__(self, runners_manager: RunnersManager):
        dbus.service.Object.__init__(
            self,
            dbus.service.BusName("org.kde.runner_general", dbus.SessionBus()),
            objpath,
        )
        self.runners_manager = runners_manager

    @dbus.service.method(iface, in_signature="s", out_signature="a(sssida{sv})")
    def Match(self, query: str):
        logger.info(f"Matching {query}")

        actions = self.runners_manager.actions()

        results = process.extract(
            query, [x.key for x in actions], scorer=fuzz.token_sort_ratio, score_cutoff=25
        )
        logger.info(f"Search results: {results}")

        output = []
        for result_key, score, _ in results:
            output.append(self.runners_manager.get_action_by_key(result_key).to_dbus_tuple(score))
        return output

    @dbus.service.method(iface, out_signature="a(sss)")
    def Actions(self):
        # id, text, icon
        return [("id", "General Runner", "run-build-configure")]

    @dbus.service.method(iface, in_signature="ss")
    def Run(self, data: str, action_id: str):
        try:
            logger.info(f"Run: {data} | {action_id}")
            command_parts = data.split(" ")
            command = command_parts[0]
            command_args = command_parts[1:]

            if command == "play-pause":
                logger.info(f"\tplay-pause: {command_args[0]}")
        except Exception as err:
            logger.exception(err)


if __name__ == "__main__":
    logging.basicConfig(filename=f"{DIR}/output.log", encoding="utf-8", level=logging.DEBUG)

    runners_manager = RunnersManager()
    print(runners_manager.actions())

    runner = DbusRunner(runners_manager)
    loop = GLib.MainLoop()
    loop.run()
