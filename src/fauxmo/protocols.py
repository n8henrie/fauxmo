"""protocols.py :: Provide asyncio protocols for UPnP and SSDP discovery."""

import asyncio
import random
import uuid
from email.utils import formatdate
from typing import cast, Iterable, Text, Tuple, Union

from fauxmo import logger
from fauxmo.plugins import FauxmoPlugin
from fauxmo.utils import make_serial


class Fauxmo(asyncio.Protocol):
    """Mimics a WeMo switch on the network.

    Aysncio protocol intended for use with BaseEventLoop.create_server.
    """

    NEWLINE = "\r\n"

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
        peername = transport.get_extra_info("peername")
        logger.debug(f"Connection made with: {peername}")
        self.transport = cast(asyncio.Transport, transport)

    def data_received(self, data: bytes) -> None:
        """Decode incoming data.

        Args:
            data: Incoming message, either setup request or action request
        """
        msg = data.decode()

        logger.debug(f"Received message:\n{msg}")
        if msg.startswith("GET /setup.xml HTTP/1.1"):
            logger.info("setup.xml requested by Echo")
            self.handle_setup()
        elif "/eventservice.xml" in msg:
            logger.info("eventservice.xml request by Echo")
            self.handle_event()
        elif "/metainfoservice.xml" in msg:
            logger.info("metainfoservice.xml request by Echo")
            self.handle_metainfo()
        elif msg.startswith("POST /upnp/control/basicevent1 HTTP/1.1"):
            logger.info("request BasicEvent1")
            self.handle_action(msg)

    def handle_setup(self) -> None:
        """Create a response to the Echo's setup request."""
        setup_xml = (
            '<?xml version="1.0"?>'
            "<root>"
            "<specVersion><major>1</major><minor>0</minor></specVersion>"
            "<device>"
            "<deviceType>urn:Belkin:device:controllee:1</deviceType>"
            f"<friendlyName>{self.name}</friendlyName>"
            "<manufacturer>Belkin International Inc.</manufacturer>"
            "<modelName>Emulated Socket</modelName>"
            "<modelNumber>3.1415</modelNumber>"
            f"<UDN>uuid:Socket-1_0-{self.serial}</UDN>"
            "<serviceList>"
            "<service>"
            "<serviceType>urn:Belkin:service:basicevent:1</serviceType>"
            "<serviceId>urn:Belkin:serviceId:basicevent1</serviceId>"
            "<controlURL>/upnp/control/basicevent1</controlURL>"
            "<eventSubURL>/upnp/event/basicevent1</eventSubURL>"
            "<SCPDURL>/eventservice.xml</SCPDURL>"
            "</service>"
            "<service>"
            "<serviceType>urn:Belkin:service:metainfo:1</serviceType>"
            "<serviceId>urn:Belkin:serviceId:metainfo1</serviceId>"
            "<controlURL>/upnp/control/metainfo1</controlURL>"
            "<eventSubURL>/upnp/event/metainfo1</eventSubURL>"
            "<SCPDURL>/metainfoservice.xml</SCPDURL>"
            "</service>"
            "</serviceList>"
            "</device>"
            "</root>"
        )

        setup_response = self.add_http_headers(setup_xml)
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
            "<s:Envelope "
            'xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
            's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
            "<s:Body>"
            "<u:{action}{action_type}Response "
            'xmlns:u="urn:Belkin:service:basicevent:1">'
            "<{action_type}>{return_val}</{action_type}>"
            "</u:{action}{action_type}Response>"
            "</s:Body>"
            "</s:Envelope>"
        ).format

        command_format = (
            'SOAPACTION: "urn:Belkin:service:basicevent:1#{}"'
        ).format

        soap_message: str = None
        action: str = None
        action_type: str = None
        return_val: str = None

        if command_format("GetBinaryState").casefold() in msg.casefold():
            logger.info(f"Attempting to get state for {self.plugin.name}")

            action = "Get"
            action_type = "BinaryState"

            try:
                state = self.plugin.get_state()
            except AttributeError:
                logger.warning(
                    f"Plugin {self.plugin.__module__} has not "
                    "implemented a `get_state` method."
                )
            else:
                logger.info(f"{self.plugin.name} state: {state}")

                success = True
                return_val = str(int(state.lower() == "on"))

        elif command_format("SetBinaryState").casefold() in msg.casefold():
            action = "Set"
            action_type = "BinaryState"

            if "<BinaryState>0</BinaryState>" in msg:
                logger.info(f"Attempting to turn off {self.plugin.name}")
                return_val = "0"
                success = self.plugin.off()

            elif "<BinaryState>1</BinaryState>" in msg:
                logger.info(f"Attempting to turn on {self.plugin.name}")
                return_val = "1"
                success = self.plugin.on()

            else:
                logger.warning(f"Unrecognized request:\n{msg}")

        elif command_format("GetFriendlyName").casefold() in msg.casefold():
            action = "Get"
            action_type = "FriendlyName"
            return_val = self.plugin.name
            success = True
            logger.info(f"{self.plugin.name} returning friendly name")

        if success:
            soap_message = soap_format(
                action=action, action_type=action_type, return_val=return_val
            )

            response = self.add_http_headers(soap_message)
            logger.debug(response)
            self.transport.write(response.encode())
        else:
            errmsg = (
                f"Unable to complete command for {self.plugin.name}:\n"
                f"{msg}"
            )
            logger.warning(errmsg)
        self.transport.close()

    def handle_metainfo(self) -> None:
        """Respond to request for metadata."""
        metainfo_xml = (
            '<scpd xmlns="urn:Belkin:service-1-0">'
            "<specVersion>"
            "<major>1</major>"
            "<minor>0</minor>"
            "</specVersion>"
            "<actionList>"
            "<action>"
            "<name>GetMetaInfo</name>"
            "<argumentList>"
            "<retval />"
            "<name>GetMetaInfo</name>"
            "<relatedStateVariable>MetaInfo</relatedStateVariable>"
            "<direction>in</direction>"
            "</argumentList>"
            "</action>"
            "</actionList>"
            "<serviceStateTable>"
            '<stateVariable sendEvents="yes">'
            "<name>MetaInfo</name>"
            "<dataType>string</dataType>"
            "<defaultValue>0</defaultValue>"
            "</stateVariable>"
            "</serviceStateTable>"
            "</scpd>"
        ) + 2 * Fauxmo.NEWLINE

        meta_response = self.add_http_headers(metainfo_xml)
        logger.debug(f"Fauxmo response to setup request:\n{meta_response}")
        self.transport.write(meta_response.encode())
        self.transport.close()

    def handle_event(self) -> None:
        """Respond to request for eventservice.xml."""
        eventservice_xml = (
            '<scpd xmlns="urn:Belkin:service-1-0">'
            "<actionList>"
            "<action>"
            "<name>SetBinaryState</name>"
            "<argumentList>"
            "<argument>"
            "<retval/>"
            "<name>BinaryState</name>"
            "<relatedStateVariable>BinaryState</relatedStateVariable>"
            "<direction>in</direction>"
            "</argument>"
            "</argumentList>"
            "</action>"
            "<action>"
            "<name>GetBinaryState</name>"
            "<argumentList>"
            "<argument>"
            "<retval/>"
            "<name>BinaryState</name>"
            "<relatedStateVariable>BinaryState</relatedStateVariable>"
            "<direction>out</direction>"
            "</argument>"
            "</argumentList>"
            "</action>"
            "</actionList>"
            "<serviceStateTable>"
            '<stateVariable sendEvents="yes">'
            "<name>BinaryState</name>"
            "<dataType>Boolean</dataType>"
            "<defaultValue>0</defaultValue>"
            "</stateVariable>"
            '<stateVariable sendEvents="yes">'
            "<name>level</name>"
            "<dataType>string</dataType>"
            "<defaultValue>0</defaultValue>"
            "</stateVariable>"
            "</serviceStateTable>"
            "</scpd>"
        ) + 2 * Fauxmo.NEWLINE

        event_response = self.add_http_headers(eventservice_xml)
        logger.debug(f"Fauxmo response to setup request:\n{event_response}")
        self.transport.write(event_response.encode())
        self.transport.close()

    @staticmethod
    def add_http_headers(xml: str) -> str:
        """Add HTTP headers to an XML body.

        Args:
            xml: XML body that needs HTTP headers
        """
        date_str = formatdate(timeval=None, localtime=False, usegmt=True)
        return (Fauxmo.NEWLINE).join(
            [
                "HTTP/1.1 200 OK",
                f'CONTENT-LENGTH: {len(xml.encode("utf8"))}',
                "CONTENT-TYPE: text/xml",
                f"DATE: {date_str}",
                "LAST-MODIFIED: Sat, 01 Jan 2000 00:01:15 GMT",
                "SERVER: Unspecified, UPnP/1.0, Unspecified",
                "X-User-Agent: Fauxmo",
                f"CONNECTION: close{Fauxmo.NEWLINE}",
                f"{xml}",
            ]
        )


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
        device_dict = {"name": name, "ip_address": ip_address, "port": port}
        self.devices.append(device_dict)

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        """Set transport attribute to incoming transport.

        Args:
            transport: Incoming asyncio.DatagramTransport
        """
        self.transport = cast(asyncio.DatagramTransport, transport)

    def datagram_received(
        self, data: Union[bytes, Text], addr: Tuple[str, int]
    ) -> None:
        """Check incoming UDP data for requests for Wemo devices.

        Args:
            data: Incoming data content
            addr: Address sending data
        """
        if isinstance(data, bytes):
            data = data.decode("utf8")

        logger.debug(f"Received data below from {addr}:")
        logger.debug(data)

        discover_patterns = [
            "ST: urn:Belkin:device:**",
            "ST: upnp:rootdevice",
            "ST: ssdp:all",
        ]

        discover_pattern = next(
            (pattern for pattern in discover_patterns if pattern in data), None
        )
        if (
            'man: "ssdp:discover"' in data.lower()
            and discover_pattern is not None
        ):
            mx = 0.0
            mx_line = next(
                (
                    line
                    for line in str(data).splitlines()
                    if line.startswith("MX: ")
                ),
                None,
            )
            if mx_line:
                mx_str = mx_line.split()[-1]
                if mx_str.replace(".", "", 1).isnumeric():
                    mx = float(mx_str)

            self.respond_to_search(addr, discover_pattern, mx)

    def respond_to_search(
        self, addr: Tuple[str, int], discover_pattern: str, mx: float = 0.0
    ) -> None:
        """Build and send an appropriate response to an SSDP search request.

        Args:
            addr: Address sending search request
        """
        date_str = formatdate(timeval=None, localtime=False, usegmt=True)
        for device in self.devices:

            name = device.get("name")
            ip_address = device.get("ip_address")
            port = device.get("port")

            location = f"http://{ip_address}:{port}/setup.xml"
            serial = make_serial(name)
            usn = (
                f"uuid:Socket-1_0-{serial}::"
                f'{discover_pattern.lstrip("ST: ")}'
            )

            response = (Fauxmo.NEWLINE).join(
                [
                    "HTTP/1.1 200 OK",
                    "CACHE-CONTROL: max-age=86400",
                    f"DATE: {date_str}",
                    "EXT:",
                    f"LOCATION: {location}",
                    'OPT: "http://schemas.upnp.org/upnp/1/0/"; ns=01',
                    f"01-NLS: {uuid.uuid4()}",
                    "SERVER: Fauxmo, UPnP/1.0, Unspecified",
                    f"{discover_pattern}",
                    f"USN: {usn}",
                ]
            ) + (2 * Fauxmo.NEWLINE)
            asyncio.ensure_future(
                self._send_async_response(response.encode("utf8"), addr, mx)
            )

    async def _send_async_response(
        self, response: bytes, addr: Tuple[str, int], mx: float = 0.0
    ) -> None:
        logger.debug(f"Sending response to {addr} with mx {mx}:\n{response}")
        await asyncio.sleep(random.random() * max(0, min(5, mx)))
        self.transport.sendto(response, addr)

    def connection_lost(self, exc: Exception) -> None:
        """Handle lost connections.

        Args:
            exc: Exception type
        """
        if exc:
            logger.warning(f"SSDPServer closed with exception: {exc}")
