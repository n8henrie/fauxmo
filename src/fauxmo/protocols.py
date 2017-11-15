"""protocols.py :: Provide asyncio protocols for UPnP and SSDP discovery."""

import asyncio
import uuid
from email.utils import formatdate
from typing import AnyStr, cast, Iterable, Tuple

from fauxmo import logger
from fauxmo.plugins import FauxmoPlugin
from fauxmo.utils import make_serial


class Fauxmo(asyncio.Protocol):
    """Mimics a WeMo switch on the network.

    Aysncio protocol intended for use with BaseEventLoop.create_server.
    """

    def __init__(self, name: str, plugin: FauxmoPlugin) -> None:
        """Initialize a Fauxmo device.

        Args:
            name: How you want to call the device, e.g. "bedroom light"
            plugin: Fauxmo plugin
        """
        self.name = name
        self.serial = make_serial(name)
        self.plugin = plugin
        self.transport: asyncio.Transport = None

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        """Accept an incoming TCP connection.

        Args:
            transport: Passed in asyncio.Transport
        """
        peername = transport.get_extra_info('peername')
        logger.debug(f"Connection made with: {peername}")
        self.transport = cast(asyncio.Transport, transport)

    def data_received(self, data: bytes) -> None:
        """Decode incoming data.

        Args:
            data: Incoming message, either setup request or action request
        """
        msg = data.decode()

        logger.debug(f"Received message:\n{msg}")
        if msg.startswith('GET /setup.xml HTTP/1.1'):
            logger.info("setup.xml requested by Echo")
            self.handle_setup()

        elif msg.startswith('POST /upnp/control/basicevent1 HTTP/1.1'):
            self.handle_action(msg)

    def handle_setup(self) -> None:
        """Create a response to the Echo's setup request."""
        date_str = formatdate(timeval=None, localtime=False, usegmt=True)

        # Made as a separate string because it requires `len(setup_xml)`
        setup_xml = (
            '<?xml version="1.0"?>'
            '<root>'
            '<device>'
            '<deviceType>urn:Fauxmo:device:controllee:1</deviceType>'
            f'<friendlyName>{self.name}</friendlyName>'
            '<manufacturer>Belkin International Inc.</manufacturer>'
            '<modelName>Emulated Socket</modelName>'
            '<modelNumber>3.1415</modelNumber>'
            f'<UDN>uuid:Socket-1_0-{self.serial}</UDN>'
            '</device>'
            '</root>'
            )

        setup_response = '\n'.join([
            'HTTP/1.1 200 OK',
            f'CONTENT-LENGTH: {len(setup_xml)}',
            'CONTENT-TYPE: text/xml',
            f'DATE: {date_str}',
            'LAST-MODIFIED: Sat, 01 Jan 2000 00:01:15 GMT',
            'SERVER: Unspecified, UPnP/1.0, Unspecified',
            'X-User-Agent: Fauxmo',
            'CONNECTION: close\n',
            f"{setup_xml}"
            ])

        logger.debug(f"Fauxmo response to setup request:\n{setup_response}")
        self.transport.write(setup_response.encode())
        self.transport.close()

    def handle_action(self, msg: str) -> None:
        """Execute `on`, `off`, or `get_state` method of plugin.

        Args:
            msg: Body of the Echo's HTTP request to trigger an action

        """
        logger.debug(f"Handling action for plugin type {self.plugin}")

        success = False
        soap_format = (
                '<s:Envelope '
                'xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
                's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
                '<s:Body>'
                '<u:{action}BinaryStateResponse '
                'xmlns:u="urn:Belkin:service:basicevent:1">'
                '<BinaryState>{state_int}</BinaryState>'
                '</u:{action}BinaryStateResponse>'
                '</s:Body>'
                '</s:Envelope>'
                ).format

        command_format = (
                'SOAPACTION: "urn:Belkin:service:basicevent:1#{}BinaryState"'
                ).format

        soap_message: str = None
        action: str = None
        state_int: int = None

        if command_format("Get") in msg:
            logger.info(f"Attempting to get state for {self.plugin.name}")

            action = "Get"

            try:
                state = self.plugin.get_state()
            except AttributeError:
                logger.warning(f"Plugin {self.plugin.__module__} has not "
                               "implemented a `get_state` method.")
            else:
                logger.info(f"{self.plugin.name} state: {state}")

                success = True
                state_int = int(state.lower() == "on")

        elif command_format("Set") in msg:
            action = "Set"

            if '<BinaryState>0</BinaryState>' in msg:
                logger.info(f"Attempting to turn off {self.plugin.name}")
                state_int = 0
                success = self.plugin.off()

            elif '<BinaryState>1</BinaryState>' in msg:
                logger.info(f"Attempting to turn on {self.plugin.name}")
                state_int = 1
                success = self.plugin.on()

            else:
                logger.warning(f"Unrecognized request:\n{msg}")

        if success:
            date_str = formatdate(timeval=None, localtime=False, usegmt=True)
            soap_message = soap_format(action=action, state_int=state_int)
            response = '\n'.join([
                'HTTP/1.1 200 OK',
                f'CONTENT-LENGTH: {len(soap_message)}',
                'CONTENT-TYPE: text/xml charset="utf-8"',
                f'DATE: {date_str}',
                'EXT:',
                'SERVER: Unspecified, UPnP/1.0, Unspecified',
                'X-User-Agent: Fauxmo',
                'CONNECTION: close\n',
                f'{soap_message}',
                ])
            logger.debug(response)
            self.transport.write(response.encode())
        else:
            errmsg = (f"Unable to complete command for {self.plugin.name}:\n"
                      f"{msg}")
            logger.warning(errmsg)
        self.transport.close()


class SSDPServer(asyncio.DatagramProtocol):
    """UDP server that responds to the Echo's SSDP / UPnP requests."""

    def __init__(self, devices: Iterable[dict] = None) -> None:
        """Initialize an SSDPServer instance.

        Args:
            devices: Iterable of devices to advertise when the Echo's SSDP
                     search request is received.
        """
        self.devices = list(devices or ())

    def add_device(self, name: str, ip_address: str, port: int) -> None:
        """Keep track of a list of devices for logging and shutdown.

        Args:
            name: Device name
            ip_address: IP address of device
            port: Port of device
        """
        device_dict = {
            'name': name,
            'ip_address': ip_address,
            'port': port
        }
        self.devices.append(device_dict)

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        """Set transport attribute to incoming transport.

        Args:
            transport: Incoming asyncio.DatagramTransport
        """
        self.transport = cast(asyncio.DatagramTransport, transport)

    # Hopefully should be fixed if PR merged:
    # https://github.com/python/typeshed/pull/1740
    def datagram_received(self, data: AnyStr,  # type: ignore
                          addr: Tuple[str, int]) -> None:
        """Check incoming UDP data for requests for Wemo devices.

        Args:
            data: Incoming data content
            addr: Address sending data
        """
        logger.debug(f"Received data below from {addr}:")
        logger.debug(str(data))

        if all(b in data for b in [b'"ssdp:discover"',
                                   b'urn:Belkin:device:**']):
            self.respond_to_search(addr)

    def respond_to_search(self, addr: Tuple[str, int]) -> None:
        """Build and send an appropriate response to an SSDP search request.

        Args:
            addr: Address sending search request
        """
        date_str = formatdate(timeval=None, localtime=False, usegmt=True)
        for device in self.devices:

            name = device.get('name')
            ip_address = device.get('ip_address')
            port = device.get('port')

            location = f'http://{ip_address}:{port}/setup.xml'
            serial = make_serial(name)
            response = '\n'.join([
                'HTTP/1.1 200 OK',
                'CACHE-CONTROL: max-age=86400',
                f'DATE: {date_str}',
                'EXT:',
                f'LOCATION: {location}',
                'OPT: "http://schemas.upnp.org/upnp/1/0/"; ns=01',
                f'01-NLS: {uuid.uuid4()}',
                'SERVER: Unspecified, UPnP/1.0, Unspecified',
                'ST: urn:Belkin:device:**',
                f'USN: uuid:Socket-1_0-{serial}::urn:Belkin:device:**',
                ]) + '\n\n'

            logger.debug(f"Sending response to {addr}:\n{response}")
            self.transport.sendto(response.encode(), addr)

    def connection_lost(self, exc: Exception) -> None:
        """Handle lost connections.

        Args:
            exc: Exception type
        """
        if exc:
            logger.warning(f"SSDPServer closed with exception: {exc}")
