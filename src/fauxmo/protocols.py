# -*- coding: utf-8 -*-
"""protocols.py

Holds asyncio protocols required classes for the Echo's UPnP / SSDP device
discovery.
"""

import asyncio
from email.utils import formatdate
import socket
import struct
import uuid

from fauxmo import logger
from fauxmo.utils import make_serial


class Fauxmo(asyncio.Protocol):
    """Mimics a WeMo switch on the network.

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


class SSDPServer(asyncio.DatagramProtocol):
    """Responds to the Echo's SSDP / UPnP requests"""

    def __init__(self, devices=None):
        """Initialize an SSDPServer instance.

        Kwargs:
            devices (list(dict)): List of devices to advertise when the Echo's
                                  SSDP search request is received.
        """

        if devices is None:
            devices = []
        self.devices = devices

    def add_device(self, name, ip_address, port):
        device_dict = {
                'name': name,
                'ip_address': ip_address,
                'port': port
                }
        self.devices.append(device_dict)

    def connection_made(self, transport):
        self.transport = transport

        # Allow receiving multicast broadcasts
        sock = self.transport.get_extra_info('socket')
        group = socket.inet_aton('239.255.255.250')
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    def datagram_received(self, data, addr):
        """Check incoming UDP data for requests for Wemo devices"""

        logger.debug("Received data below from {}:".format(addr))
        logger.debug(data)

        if all(b in data for b in [b'"ssdp:discover"',
                                   b'urn:Belkin:device:**']):
            self.respond_to_search(addr)

    def respond_to_search(self, addr):
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

    def connection_lost(self, exc):
        if exc:
            logger.warning("SSDPServer closed with exception: {}".format(exc))
