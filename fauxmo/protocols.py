"""protocols.py

Holds asyncio protocols required classes for the Echo's UPnP / SSDP device
discovery.
"""

import asyncio
from email.utils import formatdate
from typing import Iterable, AnyStr
import uuid

from . import logger
from .utils import make_serial
from .plugins import FauxmoPlugin


class Fauxmo(asyncio.Protocol):
    """Mimics a WeMo switch on the network.

    Aysncio protocol intended for use with BaseEventLoop.create_server.
    """

    def __init__(self, name: str, action_handler: FauxmoPlugin) -> None:
        """Initialize a Fauxmo device.

        Args:
            name: How you want to call the device, e.g. "bedroom light"
            action_handler: Fauxmo plugin
        """

        self.name = name
        self.serial = make_serial(name)
        self.action_handler = action_handler

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        peername = transport.get_extra_info('peername')
        logger.debug("Connection made with: {}".format(peername))

        if isinstance(transport, asyncio.Transport):
            self.transport = transport
        else:
            raise TypeError("transport should be type asyncio.Transport, got "
                            f"type {str(type(transport))}")

    def data_received(self, data: bytes) -> None:
        """Decode data and determine if it is a setup or action request"""

        msg = data.decode()

        logger.debug("Received message:\n{}".format(msg))
        if msg.startswith('GET /setup.xml HTTP/1.1'):
            logger.debug("setup.xml requested by Echo")
            self.handle_setup()

        elif msg.startswith('POST /upnp/control/basicevent1 HTTP/1.1'):
            self.handle_action(msg)

    def handle_setup(self) -> None:
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

    def handle_action(self, msg: str) -> None:
        """Execute `on` or `off` method of `action_handler`

        Args:
            msg: Body of the Echo's HTTP request to trigger an action

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


# For some reason inheriting from asyncio.DatagramProtocol ends up giving all
# kinds of problematic typing issues:
# - supertype problems if `connection_made` takes `asyncio.DatagramTransport`
# - no attribute `sendto` if it takes `asyncio.BaseTransport`
# - apparently `transport` ends up being
#   `asyncio.selector_events._SelectorDatagramTransport`, which *doesn't*
#   inherit from `asyncio.DatagramTransport`, so `isinstance` not working like
#   above in Fauxmo...
# Easiest just to not have `SSDPServer` inherit from `asyncio.DatagramProtocol`
# for now, which curiously is how they examples are in the docs -- the
# asyncio.Transport example inherits:
# https://docs.python.org/3/library/asyncio-protocol.html#tcp-echo-server-protocol
# while the Datagram example doesn't:
# https://docs.python.org/3/library/asyncio-protocol.html#udp-echo-server-protocol
class SSDPServer:
    """Responds to the Echo's SSDP / UPnP requests"""

    def __init__(self, devices: Iterable[dict]=None) -> None:
        """Initialize an SSDPServer instance.

        Args:
            devices: Iterable of devices to advertise when the Echo's SSDP
                     search request is received.
        """

        self.devices = list(devices or ())

    def add_device(self, name: str, ip_address: str, port: int) -> None:
        device_dict = {
                'name': name,
                'ip_address': ip_address,
                'port': port
                }
        self.devices.append(device_dict)

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        self.transport = transport

    def datagram_received(self, data: AnyStr, addr: str) -> None:
        """Check incoming UDP data for requests for Wemo devices"""

        logger.debug("Received data below from {}:".format(addr))
        logger.debug(str(data))

        if all(b in data for b in [b'"ssdp:discover"',
                                   b'urn:Belkin:device:**']):
            self.respond_to_search(addr)

    def respond_to_search(self, addr: str) -> None:
        """Build and send an appropriate response to an SSDP search request."""

        date_str = formatdate(timeval=None, localtime=False, usegmt=True)
        for device in self.devices:

            name = device.get('name')
            ip_address = device.get('ip_address')
            port = device.get('port')

            location = 'http://{}:{}/setup.xml'.format(ip_address, port)
            serial = make_serial(name)
            response = '\r\n'.join([
                    'HTTP/1.1 200 OK',
                    'CACHE-CONTROL: max-age=86400',
                    'DATE: {}'.format(date_str),
                    'EXT:',
                    'LOCATION: {}'.format(location),
                    'OPT: "http://schemas.upnp.org/upnp/1/0/"; ns=01',
                    '01-NLS: {}'.format(uuid.uuid4()),
                    'SERVER: Unspecified, UPnP/1.0, Unspecified',
                    'ST: urn:Belkin:device:**',
                    'USN: uuid:Socket-1_0-{}::urn:Belkin:device:**'
                    .format(serial)]) + 2 * '\r\n'

            logger.debug("Sending response to {}:\n{}".format(addr, response))
            self.transport.sendto(response.encode(), addr)

    def connection_lost(self, exc: Exception) -> None:
        if exc:
            logger.warning("SSDPServer closed with exception: {}".format(exc))
