"""fauxmo.py

Emulates a Belkin Wemo for interaction with an Amazon Echo. See README.md at
<https://github.com/n8henrie/fauxmo>.
"""

import asyncio
import importlib
import json
import logging
import pathlib
import signal
import sys
from functools import partial
from test.support import find_unused_port

from . import logger, __version__
from .plugins import FauxmoPlugin
from .protocols import SSDPServer, Fauxmo
from .utils import get_local_ip, module_from_file, make_udp_sock


def main(config_path_str: str=None, verbosity: int=20) -> None:
    """Runs the main fauxmo process

    Spawns a UDP server to handle the Echo's UPnP / SSDP device discovery
    process as well as multiple TCP servers to respond to the Echo's device
    setup requests and handle its process for turning devices on and off.

    Kwargs:
        config_path_str: Path to config file. If not given will search for
                         `config.json` in cwd, `~/.fauxmo/`, and
                         `/etc/fauxmo/`.
        verbosity: Logging verbosity, defaults to 20
    """

    logger.setLevel(verbosity)
    logger.info(f"Fauxmo version {__version__}")
    logger.debug(sys.version)

    if config_path_str:
        config_path = pathlib.Path(config_path_str)
    else:
        for config_dir in ('.', "~/.fauxmo", "/etc/fauxmo"):
            config_path = pathlib.Path(config_dir) / 'config.json'
            if config_path.is_file():
                logger.info(f"Using config: {config_path}")
                break

    try:
        config = json.loads(config_path.read_text())
    except FileNotFoundError:
        logger.error("Could not find config file in default search path. Try "
                     "specifying your file with `-c`.\n")
        raise

    # Every config should include a FAUXMO section
    fauxmo_config = config.get("FAUXMO")
    fauxmo_ip = get_local_ip(fauxmo_config.get("ip_address"))

    ssdp_server = SSDPServer()
    servers = []

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    if verbosity < 20:
        loop.set_debug(True)
        logging.getLogger('asyncio').setLevel(logging.DEBUG)

    try:
        plugins = config['PLUGINS']
    except KeyError:
        # Give a meaningful message without a nasty traceback if it looks like
        # user is running a pre-v0.4.0 config.
        errmsg = ("`PLUGINS` key not found in your config.\n"
                  "You may be trying to use an outdated config.\n"
                  "If so, please review <https://github.com/n8henrie/fauxmo> "
                  "and update your config for Fauxmo >= v0.4.0.")
        print(errmsg)
        sys.exit(1)

    for plugin in plugins:

        modname = f"{__package__}.plugins.{plugin.lower()}"
        try:
            module = importlib.import_module(modname)

        # Will fail until https://github.com/python/typeshed/pull/1083 merged
        # and included in the next mypy release
        except ModuleNotFoundError:  # type: ignore
            path_str = config['PLUGINS'][plugin]['path']
            module = module_from_file(modname, path_str)

        Plugin = getattr(module, plugin)
        if not issubclass(Plugin, FauxmoPlugin):
            raise TypeError(f"Plugins must inherit from {repr(FauxmoPlugin)}")

        # Pass along variables defined at the plugin level that don't change
        # per device
        plugin_vars = {k: v for k, v in config['PLUGINS'][plugin].items()
                       if k not in {"DEVICES", "path"}}
        logger.debug(f"plugin_vars: {repr(plugin_vars)}")

        for device in config['PLUGINS'][plugin]['DEVICES']:
            logger.debug(f"device config: {repr(device)}")

            # Ensure port is `int`, set it if not given (`None`) or 0
            device["port"] = int(device.get('port', 0)) or find_unused_port()

            try:
                plugin = Plugin(**plugin_vars, **device)
            except TypeError:
                logger.error(f"Error in plugin {repr(Plugin)}")
                raise

            fauxmo = partial(Fauxmo, name=plugin.name, plugin=plugin)
            coro = loop.create_server(fauxmo, host=fauxmo_ip, port=plugin.port)
            server = loop.run_until_complete(coro)
            servers.append(server)

            ssdp_server.add_device(plugin.name, fauxmo_ip, plugin.port)

            logger.debug(f"Started fauxmo device: {repr(fauxmo.keywords)}")

    logger.info("Starting UDP server")

    # mypy will fail until https://github.com/python/typeshed/pull/1084 merged,
    # pulled into mypy, and new mypy released
    listen = loop.create_datagram_endpoint(lambda: ssdp_server,  # type: ignore
                                           sock=make_udp_sock())
    transport, protocol = loop.run_until_complete(listen)  # type: ignore

    for signame in ('SIGINT', 'SIGTERM'):
        try:
            loop.add_signal_handler(getattr(signal, signame), loop.stop)

        # Workaround for Windows (https://github.com/n8henrie/fauxmo/issues/21)
        except NotImplementedError:
            if sys.platform == 'win32':
                pass
            else:
                raise

    loop.run_forever()

    # Will not reach this part unless SIGINT or SIGTERM triggers `loop.stop()`
    logger.debug("Shutdown starting...")
    transport.close()
    for idx, server in enumerate(servers):
        logger.debug(f"Shutting down server {idx}...")
        server.close()
        loop.run_until_complete(server.wait_closed())
    loop.close()
