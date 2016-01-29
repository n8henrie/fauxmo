# -*- coding: UTF-8 -*-
"""fauxmo.py
Emulates a Belkin Wemo for interaction with an Amazon Echo. See README.md at
<https://github.com/n8henrie/fauxmo>.
"""

from email.utils import formatdate
import logging
import os.path
import time
import uuid
import json
from .upnp import Poller, UpnpDevice, UpnpBroadcastResponder
from .handlers.rest import RestApiHandler
try:
    from .handlers.hass import HassApiHandler
except ImportError:
    # Hass not installed -- will still run fine as long as the hass portion of
    # config is disabled (or removed entirely)
    pass


logger = logging.getLogger("fauxmo")

# Minimum xml needed to define a virtual switches for the Amazon Echo


class Fauxmo(UpnpDevice):
    """Does the bulk of the work to mimic a WeMo switch on the network"""

    @staticmethod
    def make_uuid(name):
        """Create a persistent UUID from the device description"""
        return str(uuid.uuid3(uuid.NAMESPACE_X500, name))

    def __init__(self, name, listener, poller, ip_address, port,
                 action_handler=None):
        self.name = name
        self.serial = self.make_uuid(name)
        self.listener = listener
        self.poller = poller
        self.ip_address = ip_address
        self.port = port
        self.action_handler = action_handler

        self.root_url = "http://{}:{}/setup.xml"
        other_headers = ['X-User-Agent: Fauxmo']

        super().__init__(listener=self.listener, poller=self.poller,
                         port=self.port, root_url=self.root_url,
                         server_version="Unspecified, UPnP/1.0, Unspecified",
                         serial=self.serial, other_headers=other_headers,
                         ip_address=self.ip_address)
        logger.debug("Device {} ready on "
                     "{}:{}".format(self.name, self.ip_address, self.port))

    def handle_request(self, data, sender, socket):
        setup_xml = (
               '<?xml version="1.0"?>\n'
               '<root>\n'
               '<device>\n'
               '<deviceType>urn:Fauxmo:device:controllee:1</deviceType>\n'
               '<friendlyName>{}</friendlyName>\n'
               '<manufacturer>Belkin International Inc.</manufacturer>\n'
               '<modelName>Emulated Socket</modelName>\n'
               '<modelNumber>3.1415</modelNumber>\n'
               '<UDN>uuid:Socket-1_0-{}</UDN>\n'
               '</device>\n'
               '</root>'.format(self.name, self.serial)
               )
        if data.find('GET /setup.xml HTTP/1.1') == 0:
            logger.debug("setup.xml requested by Echo")

            date_str = formatdate(timeval=None, localtime=False, usegmt=True)
            msg = (
               "HTTP/1.1 200 OK\r\n"
               "CONTENT-LENGTH: {}\r\n"
               "CONTENT-TYPE: text/xml\r\n"
               "DATE: {}\r\n"
               "LAST-MODIFIED: Sat, 01 Jan 2000 00:01:15 GMT\r\n"
               "SERVER: Unspecified, UPnP/1.0, Unspecified\r\n"
               "X-User-Agent: Fauxmo\r\n"
               "CONNECTION: close\r\n"
               "\r\n"
               "{}".format(len(setup_xml), date_str, setup_xml)
               )
            logger.debug("Responding to setup request with:\n{}".format(msg))
            socket.send(msg.encode('utf8'))
        elif data.find('SOAPACTION: "urn:Belkin:service:basicevent:1#'
                       'SetBinaryState"') != -1:
            success = False

            # Turn device ON
            if data.find('<BinaryState>1</BinaryState>') != -1:
                logger.debug("Responding to ON for {}".format(self.name))
                success = self.action_handler.on()

            # Turn device OFF
            elif data.find('<BinaryState>0</BinaryState>') != -1:
                logger.debug("Responding to OFF for {}".format(self.name))
                success = self.action_handler.off()

            else:
                logger.debug("Unknown Binary State request:")
                logger.debug(data)

            if success:
                # The echo is happy with the 200 status code and doesn't
                # appear to care about the SOAP response body
                soap = ""
                date_str = formatdate(timeval=None, localtime=False,
                                      usegmt=True)
                msg = ("HTTP/1.1 200 OK\r\n"
                       "CONTENT-LENGTH: {}\r\n"
                       "CONTENT-TYPE: text/xml charset=\"utf-8\"\r\n"
                       "DATE: {}\r\n"
                       "EXT:\r\n"
                       "SERVER: Unspecified, UPnP/1.0, Unspecified\r\n"
                       "X-User-Agent: Fauxmo\r\n"
                       "CONNECTION: close\r\n"
                       "\r\n"
                       "{}".format(len(soap), date_str, soap))
                logger.debug(msg)
                socket.send(msg.encode('utf8'))
        else:
            logger.debug(data)


def main(config_path=None, verbosity=20):
    logger.setLevel(verbosity)

    # Set up our singleton for polling the sockets for data ready
    poller = Poller()

    # Set up our singleton listener for UPnP broadcasts
    listener = UpnpBroadcastResponder()
    listener.init_socket()

    # Add the UPnP broadcast listener to the poller so we can respond
    # when a broadcast is received.
    poller.add(listener)

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
    ip_address = fauxmo_config.get("ip_address")

    # Initialize Fauxmo devices
    for device in config.get('DEVICES'):
        name = device.get('description')
        port = int(device.get("port", 0))
        action_handler = RestApiHandler(**device.get("handler"))
        fauxmo = Fauxmo(name=name, listener=listener, poller=poller,
                        ip_address=ip_address, port=port,
                        action_handler=action_handler)
        logger.debug(vars(fauxmo))

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
            action_handler = HassApiHandler(host=hass_host,
                                            password=hass_password,
                                            entity=entity, port=hass_port)
            fauxmo = Fauxmo(name=name, listener=listener, poller=poller,
                            ip_address=ip_address, port=device_port,
                            action_handler=action_handler)
            logger.debug(vars(fauxmo))

    logger.debug("Entering main loop (polling)")
    while True:
        try:
            # Allow time for a ctrl-c to stop the process
            poller.poll(100)
            time.sleep(0.1)
        except Exception:
            logger.error("Exception during polling")
            raise
