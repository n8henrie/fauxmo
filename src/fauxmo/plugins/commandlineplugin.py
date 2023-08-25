"""Fauxmo plugin that runs a command on the local machine.

Runs a command using `subprocess.run`. Caveat emptor: there may be major
security risks to running this plugin, as it enables Fauxmo to run
semi-arbitrary code, depending on your configuration. By enabling or using it,
you acknowledge that it could run commands from your config.json that could
lead to data compromise, corruption, loss, etc. Consider making your
config.json read-only. If there are parts of this you don't understand, you
should probably not use this plugin.

If the command runs with a return code of 0, Alexa should respond prompty
"Okay" or something that indicates it seems to have worked. If the command has
a return code of anything other than 0, Alexa stalls for several seconds and
subsequently reports that there was a problem (which should notify the user
that something didn't go as planned).

TODO: Consider making this use `asyncio.subprocess` eventually, but that would
require `run_cmd` to be an async function, which would then infect the rest of
the app with `async`.

Example config:

```json
{
  "FAUXMO": {
    "ip_address": "auto"
  },
  "PLUGINS": {
    "CommandLinePlugin": {
      "timeout": 5,
      "DEVICES": [
        {
            "name": "output stuff to a file",
            "port": 49915,
            "on_cmd": "touch testfile.txt",
            "off_cmd": "rm testfile.txt",
            "state_cmd": "ls testfile.txt",
            "timeout": 2
        },
        {
            "name": "command with fake state",
            "port": 49916,
            "on_cmd": "touch testfile.txt",
            "off_cmd": "rm testfile.txt",
            "use_fake_state": true
        }
      ]
    }
  }
}
```
"""

from __future__ import annotations

import shlex
import subprocess
import typing as t

from fauxmo import logger
from fauxmo.plugins import FauxmoPlugin


class CommandLinePlugin(FauxmoPlugin):
    """Fauxmo Plugin for running commands on the local machine."""

    def __init__(
        self,
        name: str,
        port: int,
        on_cmd: str,
        off_cmd: str,
        state_cmd: str | None = None,
        timeout: int | None = None,
        shell: bool = False,
        use_fake_state: bool = False,
    ) -> None:
        """Initialize a CommandLinePlugin instance.

        Args:
            name: Name for this Fauxmo device
            port: Port on which to run a specific CommandLinePlugin instance
            on_cmd: Command to be called when turning device on
            off_cmd: Command to be called when turning device off
            state_cmd: Command to check device state (return code 0 == on)
            timeout: Timeout in seconds
            shell: Whether or not to run the command with `shell=True`
            use_fake_state: If `True`, override `get_state` to return the
                            latest action as the device state. NB: The proper
                            json boolean value for Python's `True` is `true`,
                            not `True` or `"true"`.

        """
        self.on_cmd = on_cmd
        self.off_cmd = off_cmd
        self.state_cmd = state_cmd
        self.shell = shell
        self.timeout = timeout

        self.use_fake_state = use_fake_state

        super().__init__(name=name, port=port)

    def run_cmd(self, cmd: str) -> bool:
        """Partialmethod to run command.

        Args:
            cmd: Command to be run
        Returns:
            True if command seems to have run without error

        """
        # Workaround for type hints, as `shell=True` expects a string and
        # `shell=False` expects a list
        cmd_list: str | t.List[str] = cmd
        if not self.shell:
            cmd_list = shlex.split(cmd)

        try:
            process = subprocess.run(
                cmd_list, timeout=self.timeout, shell=self.shell
            )
        except subprocess.TimeoutExpired as e:
            logger.exception(e)
            return False

        return process.returncode == 0

    def on(self) -> bool:
        """Run on command.

        Returns:
            True if command seems to have run without error.

        """
        return self.run_cmd(self.on_cmd)

    def off(self) -> bool:
        """Run off command.

        Returns:
            True if command seems to have run without error.

        """
        return self.run_cmd(self.off_cmd)

    def get_state(self) -> str:
        """Get device state.

        NB: Return code of `0` (i.e. ran without error) indicates "on" state,
        otherwise will be off. making it easier to have something like `ls
        path/to/pidfile` suggest `on`. Many command line switches may not
        actually have a "state" per se (just an arbitary command you want to
        run), in which case you could just put "false" as the command, which
        should always return "off".

        Returns:
            "on" or "off" if `state_cmd` is defined, "unknown" if undefined

        """
        if self.use_fake_state is True:
            return super().get_state()

        if self.state_cmd is None:
            return "unknown"

        returned_zero = self.run_cmd(self.state_cmd)
        if returned_zero is True:
            return "on"
        return "off"
