"""fauxmo.py

Emulates a Belkin Wemo for interaction with an Amazon Echo. See README.md at
<https://github.com/n8henrie/fauxmo>.
"""

import asyncio
import importlib
import json
import pathlib
import signal
import socket
import sys
from functools import partial
from test.support import find_unused_port

import fauxmo.plugins
from fauxmo import logger
from fauxmo.protocols import SSDPServer, Fauxmo
from fauxmo.utils import get_local_ip, module_from_file


def main(config_path=None, verbosity=20):
    """Runs the main fauxmo process

    Spawns a UDP server to handle the Echo's UPnP / SSDP device discovery
    process as well as multiple TCP servers to respond to the Echo's device
    setup requests and handle its process for turning devices on and off.

    Kwargs:
        config_path (str): Path to config file. If not given will search for
                           `config.json` in cwd, `~/.fauxmo/`, and
                           `/etc/fauxmo/`.
        verbosity (int): Logging verbosity, defaults to 20
    """

    logger.setLevel(verbosity)

    logger.debug(sys.version)

    if not config_path:
        config_dirs = ['.', os.path.expanduser("~/.fauxmo"), "/etc/fauxmo"]
        for config_dir in config_dirs:
            config_path = os.path.join(config_dir, 'config.json')
            if os.path.isfile(config_path):
                logger.info("Using config: {}".format(config_path))
                break

    try:
        with open(config_path) as config_file:
            config = json.load(config_file)
    except FileNotFoundError:
        logger.error("Could not find config file in default search path. "
                     "Try specifying your file with `-c` flag.\n")
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

    for plugin in config['PLUGINS']:

        modname = f"{__package__}.plugins.{plugin.lower()}"
        try:
            module = importlib.import_module(modname)
        except ModuleNotFoundError:
            path_str = config['PLUGINS'][plugin]['path']
            module = module_from_file(modname, path_str)

        Plugin = getattr(module, plugin)

        # Pass along variables defined at the plugin level that don't change
        # per device
        plugin_vars = {k: v for k, v in config['PLUGINS'][plugin].items()
                       if k not in {"DEVICES", "path"}}
        logger.debug(f"plugin_vars: {repr(plugin_vars)}")

        for device in config['PLUGINS'][plugin]['DEVICES']:
            logger.debug(f"device: {repr(device)}")
            name = device['name']

            # Ensure port is `int`, set it if not given (`None`) or 0
            device["port"] = int(device.get('port', 0)) or find_unused_port()

            try:
                plugin = Plugin(**plugin_vars, **device)
            except TypeError:
                logger.error(f"Error in plugin {repr(Plugin)}")
                raise

            fauxmo = partial(Fauxmo, name=name, action_handler=plugin)
            coro = loop.create_server(fauxmo, host=fauxmo_ip, port=plugin.port)
            server = loop.run_until_complete(coro)
            servers.append(server)

            ssdp_server.add_device(name, fauxmo_ip, plugin.port)

            logger.debug(f"fauxmo keywords: {repr(fauxmo.keywords)}")

    logger.info("Starting UDP server")

    listen = loop.create_datagram_endpoint(
            lambda: ssdp_server,
            local_addr=('0.0.0.0', 1900),
            family=socket.AF_INET
            )
    transport, protocol = loop.run_until_complete(listen)

    for signame in ('SIGINT', 'SIGTERM'):
        try:
            loop.add_signal_handler(getattr(signal, signame), loop.stop)

        # Workaround for Windows (https://github.com/n8henrie/fauxmo/issues/21)
        except NotImplementedError:
            pass

    loop.run_forever()

    # Will not reach this part unless SIGINT or SIGTERM triggers `loop.stop()`
    logger.debug("Shutdown starting...")
    transport.close()
    for idx, server in enumerate(servers):
        logger.debug("Shutting down server {}...".format(idx))
        server.close()
        loop.run_until_complete(server.wait_closed())
    loop.close()
