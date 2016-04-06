# -*- coding: utf-8 -*-
"""upnp.py

Holds required classes for the Echo's UPnP / SSDP device discovery.
"""

import asyncio
from email.utils import formatdate
import uuid

from fauxmo import logger
from fauxmo.utils import make_serial


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

    def datagram_received(self, data, addr):
        """Check incoming UDP data for requests for Wemo devices"""

        msg = data.decode()
        logger.debug("Received from {}:\n{}".format(addr, msg))

        if 'urn:Belkin:device:**' in msg:
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
            self.transport.sendto(response.encode('utf8'), addr)

    def connection_lost(self, exc):
        if exc:
            logger.warning("SSDPServer closed with exception: {}".format(exc))
