"""upnp.py
Holds required classes for UPnP for fauxmo.
"""

import logging
import select
import socket
import uuid
from email.utils import formatdate
import struct
import time

logger = logging.getLogger("fauxmo")


class Poller:
    def __init__(self):
        if 'poll' in dir(select):
            self.use_poll = True
            self.poller = select.poll()
        else:
            self.use_poll = False
        self.targets = {}

    def add(self, target, fileno=None):
        if not fileno:
            fileno = target.fileno()
        if self.use_poll:
            self.poller.register(fileno, select.POLLIN)
        self.targets[fileno] = target

    def remove(self, target, fileno=None):
        if not fileno:
            fileno = target.fileno()
        if self.use_poll:
            self.poller.unregister(fileno)
        del(self.targets[fileno])

    def poll(self, timeout=0):
        if self.use_poll:
            ready = self.poller.poll(timeout)
        else:
            ready = []
            if len(self.targets) > 0:
                (rlist, wlist, xlist) = select.select(self.targets.keys(), [],
                                                      [], timeout)
                ready = [(x, None) for x in rlist]
        for one_ready in ready:
            target = self.targets.get(one_ready[0])
            if target:
                target.do_read(one_ready[0])


# Base class for a generic UPnP device. This is far from complete
# but it supports either specified or automatic IP address and port
# selection.

class UpnpDevice:
    def __init__(self, listener, poller, port, root_url, server_version,
                 serial, other_headers=None, ip_address=None):
        self.listener = listener
        self.poller = poller
        self.port = port
        self.root_url = root_url
        self.server_version = server_version
        self.serial = serial
        self.uuid = uuid.uuid4()
        self.other_headers = other_headers

        self.ip_address = UpnpDevice.get_local_ip(ip_address)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logger.debug("Attempting to bind: {}:{}".format(self.ip_address,
                                                        self.port))

        try:
            self.socket.bind((self.ip_address, self.port))
        except socket.gaierror:
            errmsg = ("Couldn't bind {}:{}. Please review your config "
                     "settings".format(self.ip_address, self.port))
            logger.error(errmsg)
            raise

        self.socket.listen(5)
        if self.port == 0:
            self.port = self.socket.getsockname()[1]
        self.poller.add(self)
        self.client_sockets = {}
        self.listener.add_device(self)

    @staticmethod
    def get_local_ip(ip_address=None):
        if ip_address is None or str(ip_address).lower() == "auto":
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

    def fileno(self):
        return self.socket.fileno()

    def do_read(self, fileno):
        if fileno == self.socket.fileno():
            (client_socket, client_address) = self.socket.accept()
            self.poller.add(self, client_socket.fileno())
            self.client_sockets[client_socket.fileno()] = client_socket
        else:
            data, sender = self.client_sockets[fileno].recvfrom(4096)
            data = data.decode('utf8')
            if not data:
                self.poller.remove(self, fileno)
                del(self.client_sockets[fileno])
            else:
                self.handle_request(data, sender, self.client_sockets[fileno])

    def respond_to_search(self, destination, search_target):
        logger.debug("Responding to search")
        date_str = formatdate(timeval=None, localtime=False, usegmt=True)
        location_url = self.root_url.format(self.ip_address, self.port)
        message_dict = {
            "date_str": date_str,
            "location_url": location_url,
            "uuid": self.uuid,
            "server_version": self.server_version,
            "search_target": search_target,
            "serial": self.serial
            }

        message = ('HTTP/1.1 200 OK\r\n'
                   'CACHE-CONTROL: max-age=86400\r\n'
                   'DATE: {date_str}\r\n'
                   'EXT:\r\n'
                   'LOCATION: {location_url}\r\n'
                   'OPT: "http://schemas.upnp.org/upnp/1/0/"; ns=01\r\n'
                   '01-NLS: {uuid}\r\n'
                   'SERVER: {server_version}\r\n'
                   'ST: {search_target}\r\n'
                   'USN: uuid:Socket-1_0-{serial}::'
                   '{search_target}\r\n'.format(**message_dict))

        if self.other_headers:
            for header in self.other_headers:
                message += "{}\r\n".format(header)
        message += "\r\n"
        logger.debug(message)
        temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        temp_socket.sendto(message.encode('utf8'), destination)


# Since we have a single process managing several virtual UPnP devices,
# we only need a single listener for UPnP broadcasts. When a matching
# search is received, it causes each device instance to respond.
#
# Note that this is currently hard-coded to recognize only the search
# from the Amazon Echo for WeMo devices. In particular, it does not
# support the more common root device general search. The Echo
# doesn't search for root devices.

class UpnpBroadcastResponder:
    TIMEOUT = 0

    def __init__(self):
        self.devices = []

    def init_socket(self):
        ok = True
        self.ip = '239.255.255.250'
        self.port = 1900
        try:
            # Needed to join a multicast group
            self.mreq = struct.pack("4sl", socket.inet_aton(self.ip),
                                    socket.INADDR_ANY)

            # Set up server socket
            self.ssock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                       socket.IPPROTO_UDP)
            self.ssock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            try:
                self.ssock.bind(('', self.port))
            except Exception:
                logger.exception("Failed to bind {}:{}: {}".format(self.ip,
                                                                   self.port))
                ok = False

            try:
                self.ssock.setsockopt(socket.IPPROTO_IP,
                                      socket.IP_ADD_MEMBERSHIP, self.mreq)
            except Exception:
                logger.exception('WARNING: Failed to join multicast group:')
                ok = False

        except Exception:
            logger.exception("Failed to initialize UPnP sockets:")
            return False
        if ok:
            logger.debug("Listening for UPnP broadcasts")

    def fileno(self):
        return self.ssock.fileno()

    def do_read(self, fileno):
        data, sender = self.recvfrom(1024)
        # data = data.decode('utf8')
        if data:
            if data.find('M-SEARCH') == 0 and \
                    data.find('urn:Belkin:device:**') != -1:
                for device in self.devices:
                    time.sleep(0.1)
                    device.respond_to_search(sender, 'urn:Belkin:device:**')
            else:
                pass

    # Receive network data
    def recvfrom(self, size):
        if self.TIMEOUT:
            self.ssock.setblocking(0)
            ready = select.select([self.ssock], [], [], self.TIMEOUT)[0]
        else:
            self.ssock.setblocking(1)
            ready = True

        try:
            if ready:
                data, address = self.ssock.recvfrom(size)
                data = data.decode('utf8')
                return data, address
            else:
                return False, False
        except Exception as e:
            logger.debug(e)
            return False, False

    def add_device(self, device):
        self.devices.append(device)
        logger.debug("UPnP broadcast listener: new device registered")
