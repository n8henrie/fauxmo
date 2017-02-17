"""fauxmo.py

Emulates a Belkin Wemo for interaction with an Amazon Echo. See README.md at
<https://github.com/n8henrie/fauxmo>.
"""

import asyncio
from functools import partial
import json
import os.path
import signal
import socket
import sys

from fauxmo import logger
from fauxmo.handlers.hass import HassAPIHandler
from fauxmo.handlers.rest import RESTAPIHandler
from fauxmo.protocols import SSDPServer, Fauxmo
from fauxmo.utils import get_local_ip


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
    loop.set_debug(True)

    # Initialize Fauxmo devices
    for device in config.get('DEVICES', {}):
        name = device.get('description')
        port = int(device.get("port"))
        action_handler = RESTAPIHandler(**device.get("handler"))

        fauxmo = partial(Fauxmo, name=name, action_handler=action_handler)
        coro = loop.create_server(fauxmo, host=fauxmo_ip, port=port)
        server = loop.run_until_complete(coro)
        servers.append(server)

        ssdp_server.add_device(name, fauxmo_ip, port)

        logger.debug(fauxmo.keywords)

    # Initialize Home Assistant devices if config exists and enable is True
    if config.get("HOMEASSISTANT", {}).get("enable") is True:
        hass_config = config.get("HOMEASSISTANT")

        hass_host = hass_config.get("host")
        hass_password = hass_config.get("password")
        hass_port = hass_config.get("port")

        for device in hass_config.get('DEVICES'):
            name = device.get('description')
            device_port = device.get("port")
            entity = device.get("entity_id")
            action_handler = HassAPIHandler(host=hass_host,
                                            password=hass_password,
                                            entity=entity, port=hass_port)
            fauxmo = partial(Fauxmo, name=name, action_handler=action_handler)
            coro = loop.create_server(fauxmo, host=fauxmo_ip, port=device_port)
            server = loop.run_until_complete(coro)
            servers.append(server)

            ssdp_server.add_device(name, fauxmo_ip, device_port)

            logger.debug(fauxmo.keywords)

    logger.info("Starting UDP server")

    listen = loop.create_datagram_endpoint(lambda: ssdp_server,
                                           local_addr=('0.0.0.0', 1900),
                                           family=socket.AF_INET)
    transport, protocol = loop.run_until_complete(listen)

    for signame in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(getattr(signal, signame), loop.stop)

    loop.run_forever()

    # Will not reach this part unless SIGINT or SIGTERM triggers `loop.stop()`
    logger.debug("Shutdown starting...")
    transport.close()
    for idx, server in enumerate(servers):
        logger.debug("Shutting down server {}...".format(idx))
        server.close()
        loop.run_until_complete(server.wait_closed())
    loop.close()
