# -*- coding: utf-8 -*-
"""fauxmo.py
Emulates a Belkin Wemo for interaction with an Amazon Echo. See README.md at
<https://github.com/n8henrie/fauxmo>.
"""

import asyncio
from email.utils import formatdate
from functools import partial
import json
import os.path
import signal

from fauxmo import logger
from fauxmo.handlers.rest import RESTAPIHandler
from fauxmo.upnp import SSDPServer
from fauxmo.utils import make_udp_sock, get_local_ip, make_serial
try:
    from fauxmo.handlers.hass import HassAPIHandler
except ImportError:
    # Hass not installed -- will still run fine as long as the hass portion of
    # config is disabled (or removed entirely)
    pass


class Fauxmo(asyncio.Protocol):
    """Mimics a WeMo switch on the network

    Aysncio protocol intended for use with BaseEventLoop.create_server.
    """

    def __init__(self, name, action_handler):
        """Initialize a Fauxmo device.

        Args:
            name (str): How you want to call the device, e.g. "bedroom light"
            action_handler (fauxmo.handler): Fauxmo action handler object
        """

        self.name = name
        self.serial = make_serial(name)
        self.action_handler = action_handler

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        logger.debug("Connection made with: {}".format(peername))
        self.transport = transport

    def data_received(self, data):
        """Decode data and determine if it is a setup or action request"""

        msg = data.decode()
        logger.debug("Received message:\n{}".format(msg))
        if msg.startswith('GET /setup.xml HTTP/1.1'):
            logger.debug("setup.xml requested by Echo")
            self.handle_setup()

        elif msg.startswith('POST /upnp/control/basicevent1 HTTP/1.1'):
            self.handle_action(msg)

    def handle_setup(self):
        """Create a response to the Echo's setup request"""

        date_str = formatdate(timeval=None, localtime=False, usegmt=True)

        setup_xml = '\r\n'.join([
               '<?xml version="1.0"?>',
               '<root>',
               '<device>',
               '<deviceType>urn:Fauxmo:device:controllee:1</deviceType>',
               '<friendlyName>{}</friendlyName>'.format(self.name),
               '<manufacturer>Belkin International Inc.</manufacturer>',
               '<modelName>Emulated Socket</modelName>',
               '<modelNumber>3.1415</modelNumber>',
               '<UDN>uuid:Socket-1_0-{}</UDN>'.format(self.serial),
               '</device>',
               '</root>']) + 2 * '\r\n'

        # Made as a separate string because it requires `len(setup_xml)`
        setup_response = '\r\n'.join([
               'HTTP/1.1 200 OK',
               'CONTENT-LENGTH: {}'.format(len(setup_xml)),
               'CONTENT-TYPE: text/xml',
               'DATE: {}'.format(date_str),
               'LAST-MODIFIED: Sat, 01 Jan 2000 00:01:15 GMT',
               'SERVER: Unspecified, UPnP/1.0, Unspecified',
               'X-User-Agent: Fauxmo',
               'CONNECTION: close']) + 2 * '\r\n' + setup_xml

        logger.debug("Fauxmo response to setup request:\n{}"
                     .format(setup_response))
        self.transport.write(setup_response.encode())
        self.transport.close()

    def handle_action(self, msg):
        """Execute `on` or `off` method of `action_handler`

        Args:
            msg (str): Body of the Echo's HTTP request to trigger an action

        """

        success = False
        if '<BinaryState>0</BinaryState>' in msg:
            # `off()` method called
            success = self.action_handler.off()

        elif '<BinaryState>1</BinaryState>' in msg:
            # `on()` method called
            success = self.action_handler.on()

        else:
            logger.debug("Unrecognized request:\n{}".format(msg))

        if success:
            date_str = formatdate(timeval=None, localtime=False, usegmt=True)
            response = '\r\n'.join([
                    'HTTP/1.1 200 OK',
                    'CONTENT-LENGTH: 0',
                    'CONTENT-TYPE: text/xml charset="utf-8"',
                    'DATE: {}'.format(date_str),
                    'EXT:',
                    'SERVER: Unspecified, UPnP/1.0, Unspecified',
                    'X-User-Agent: Fauxmo',
                    'CONNECTION: close']) + 2 * '\r\n'
            logger.debug(response)
            self.transport.write(response.encode())
            self.transport.close()


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

    loop = asyncio.get_event_loop()
    loop.set_debug(True)

    # Initialize Fauxmo devices
    for device in config.get('DEVICES'):
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
                                           sock=make_udp_sock())
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
