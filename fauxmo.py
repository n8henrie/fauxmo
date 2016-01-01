#! /usr/bin/env python3
# -*- coding: UTF-8 -*-
"""fauxmo.py
Emulates a Belkin Wemo for interaction with an Amazon Echo. See README.md at
<https://github.com/n8henrie/fauxmo>.
"""

from email.utils import formatdate
import requests
import select
import socket
import struct
import time
import uuid
import logging
import json
import sys
import argparse
try:
    import homeassistant.remote
    from homeassistant.const import SERVICE_TURN_ON, SERVICE_TURN_OFF
except ImportError:
    # Hass not installed -- will still run fine as long as the hass portion of
    # config is disabled (or removed entirely)
    pass


# Minimum xml needed to define a virtual switches for the Amazon Echo
SETUP_XML = """<?xml version="1.0"?>
<root>
  <device>
    <deviceType>urn:MakerMusings:device:controllee:1</deviceType>
    <friendlyName>{device_name}</friendlyName>
    <manufacturer>Belkin International Inc.</manufacturer>
    <modelName>Emulated Socket</modelName>
    <modelNumber>3.1415</modelNumber>
    <UDN>uuid:Socket-1_0-{device_serial}</UDN>
  </device>
</root>
"""


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
            logger.debug(one_ready)
            logger.debug(ready)
            logger.debug(self.targets)
            target = self.targets.get(one_ready[0])
            if target:
                target.do_read(one_ready[0])


# Base class for a generic UPnP device. This is far from complete
# but it supports either specified or automatic IP address and port
# selection.

class UpnpDevice:
    this_host_ip = None

    @staticmethod
    def local_ip_address():
        if not UpnpDevice.this_host_ip:
            hostname = socket.gethostname()
            UpnpDevice.this_host_ip = socket.gethostbyname(hostname)
            logger.debug("got local address of "
                         "{}".format(UpnpDevice.this_host_ip))
        return UpnpDevice.this_host_ip

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

        if ip_address:
            self.ip_address = ip_address
        else:
            self.ip_address = UpnpDevice.local_ip_address()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logger.debug("Attempting to bind: {}:{}".format(self.ip_address,
                                                        self.port))
        self.socket.bind((self.ip_address, self.port))
        self.socket.listen(5)
        if self.port == 0:
            self.port = self.socket.getsockname()[1]
        self.poller.add(self)
        self.client_sockets = {}
        self.listener.add_device(self)

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


class Fauxmo(UpnpDevice):
    """Does the bulk of the work to mimic a WeMo switch on the network"""

    @staticmethod
    def make_uuid(name):
        """Create a persistent UUID from the device description"""
        return name[:3]
        # return str(uuid.uuid3(uuid.NAMESPACE_X500, name))

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
        if data.find('GET /setup.xml HTTP/1.1') == 0:
            xml_dict = {'device_name': self.name,
                        'device_serial': self.serial}
            logger.debug("Responding to setup.xml with {}".format(xml_dict))
            xml = SETUP_XML.format(**xml_dict)
            logger.debug(xml)
            date_str = formatdate(timeval=None, localtime=False, usegmt=True)
            message = ("HTTP/1.1 200 OK\r\n"
                       "CONTENT-LENGTH: {}\r\n"
                       "CONTENT-TYPE: text/xml\r\n"
                       "DATE: {}\r\n"
                       "LAST-MODIFIED: Sat, 01 Jan 2000 00:01:15 GMT\r\n"
                       "SERVER: Unspecified, UPnP/1.0, Unspecified\r\n"
                       "X-User-Agent: Fauxmo\r\n"
                       "CONNECTION: close\r\n"
                       "\r\n"
                       "{}".format(len(xml), date_str, xml))
            logger.debug(message)
            socket.send(message.encode('utf8'))
        elif data.find('SOAPACTION: "urn:Belkin:service:basicevent:1#'
                       'SetBinaryState"') != -1:
            success = False
            if data.find('<BinaryState>1</BinaryState>') != -1:
                # on
                logger.debug("Responding to ON for {}".format(self.name))
                success = self.action_handler.on()
            elif data.find('<BinaryState>0</BinaryState>') != -1:
                # off
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
                message = ("HTTP/1.1 200 OK\r\n"
                           "CONTENT-LENGTH: {}\r\n"
                           "CONTENT-TYPE: text/xml charset=\"utf-8\"\r\n"
                           "DATE: {}\r\n"
                           "EXT:\r\n"
                           "SERVER: Unspecified, UPnP/1.0, Unspecified\r\n"
                           "X-User-Agent: Fauxmo\r\n"
                           "CONNECTION: close\r\n"
                           "\r\n"
                           "{}".format(len(soap), date_str, soap))
                logger.debug(message)
                socket.send(message.encode('utf8'))
        else:
            logger.debug(data)


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


class RestApiHandler:
    """Rest API handler class.

    The Fauxmo class expects handlers to be instances of objects that have on()
    and off() methods that return True on success and False otherwise.  This
    example class takes two full URLs that should be requested when an on and
    off command are invoked respectively. It ignores any return data.
    """

    def __init__(self, on_cmd, off_cmd, method=None, json=None, headers=None):
        self.on_cmd = on_cmd
        self.off_cmd = off_cmd
        self.method = method
        self.json = json
        self.headers = headers

    def on(self):
        if self.method == "POST":
            r = requests.post(self.on_cmd, json=self.json,
                              headers=self.headers)
        else:
            r = requests.get(self.on_cmd, headers=self.headers)
        return r.status_code in [200, 201]

    def off(self):
        if self.method == "POST":
            r = requests.post(self.off_cmd, json=self.json,
                              headers=self.headers)
        else:
            r = requests.get(self.off_cmd, headers=self.headers)
        return r.status_code in [200, 201]


class HassApiHandler:
    """Handler for Home Assistant (hass) Python API.

    Allows users to specify Home Assistant services in their config.json and
    toggle these with the Echo. While this can be done with Home Assistant's
    REST API as well (example included), I find it easier to use the Python
    API.

    args:
    host -- IP address running HA  e
    password -- hass password
    entity -- entity_id used by hass, one easy way to find is to curl and grep
              the REST API, eg `curl http://IP/api/bootstrap | grep entity_id`

    kwargs:
    port -- the port running hass on the host computer (default 8123)
    """

    def __init__(self, host, password, entity, port=8123):
        self.host = host
        self.password = password
        self.entity = entity
        self.port = port

        self.domain = self.entity.split(".")[0]
        self.api = homeassistant.remote.API(self.host, self.password,
                                            port=self.port)

    def send(self, signal):
        """Send a signal to the hass `call_service` function, returns True.

        The hass Python API doesn't appear to return anything with this
        function, but will raise an exception if things didn't seem to work, so
        I have it set to just return True, hoping for an exception if there was
        a problem.

        args:
        signal -- signal imported from homeassistant.const. I have imported
                  SERVICE_TURN_ON and SERVICE_TURN_OFF, make sure you import
                  any others that you need.
        """

        homeassistant.remote.call_service(self.api, self.domain, signal,
                                          {'entity_id': self.entity})
        return True

    def on(self):
        return self.send(SERVICE_TURN_ON)

    def off(self):
        return self.send(SERVICE_TURN_OFF)


def main(args):
    if args.verbose:
        logger.setLevel(level=logging.DEBUG)

    # Set up our singleton for polling the sockets for data ready
    poller = Poller()

    # Set up our singleton listener for UPnP broadcasts
    listener = UpnpBroadcastResponder()
    listener.init_socket()

    # Add the UPnP broadcast listener to the poller so we can respond
    # when a broadcast is received.
    poller.add(listener)

    with open('config.json') as config_file:
        config = json.load(config_file)

    # Initialize Fauxmo devices
    for device in config.get('DEVICES'):
        name = device.get('description')
        port = int(device.get("port", 0))
        action_handler = RestApiHandler(**device.get("handler"))
        fauxmo = Fauxmo(name=name, listener=listener, poller=poller,
                        ip_address=None, port=port,
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
                            ip_address=None, port=device_port,
                            action_handler=action_handler)
            logger.debug(vars(fauxmo))

    logger.debug("Entering main loop (polling)")
    while True:
        try:
            # Allow time for a ctrl-c to stop the process
            poller.poll(100)
            time.sleep(0.1)
        except Exception:
            logger.exception("Exception during polling")
            raise


def _cli():
    """Parse command line options, provide entry point for console scripts"""

    arguments = sys.argv[1:]
    parser = argparse.ArgumentParser(description="Emulate Belkin Wemo devices "
                                     "for use with Amaazon Echo")
    parser.add_argument("-v", "--verbose", help="toggle verbose output",
                        action="store_true")
    args = parser.parse_args(arguments)
    main(args)


if __name__ == "__main__":
    logging.basicConfig(
            level=logging.WARNING,
            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
            )
    logger = logging.getLogger()
    logger.addHandler(logging.NullHandler())

    _cli()
