# -*- coding: utf-8 -*-
"""utils.py

Utility functions for Fauxmo.
"""

import struct
import socket
from fauxmo import logger
import uuid


def make_udp_sock():
    """Make a suitable udp socket to listen for device discovery requests"""

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 1900))
    group = socket.inet_aton('239.255.255.250')
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Raises AttributeError on some Unixes
    if hasattr(socket, 'SO_REUSEPORT'):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    return sock


def get_local_ip(ip_address):
    """Attempt to get the local network-connected IP address"""

    if ip_address is None or ip_address.lower() == "auto":
        logger.debug("Attempting to get IP address automatically")

        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)

        # Workaround for Linux returning localhost
        # See: SO question #166506 by @UnkwnTech
        if ip_address in ['127.0.1.1', '127.0.0.1', 'localhost']:
            tempsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            tempsock.connect(('8.8.8.8', 0))
            ip_address = tempsock.getsockname()[0]
            tempsock.close()

    logger.debug("Using IP address: {}".format(ip_address))
    return ip_address


def make_serial(name):
    """Create a persistent UUID from the device name

    Returns a suitable UUID derived from `name`. Should remain static for a
    given name.

    Args:
        name (str): Friendly device name (e.g. "living room light")
    """

    return str(uuid.uuid3(uuid.NAMESPACE_X500, name))
