"""utils.py :: Holds utility functions for Fauxmo."""

import importlib.util
import pathlib
import socket
import struct
import sys
import uuid
from types import ModuleType

from fauxmo import logger


def get_local_ip(ip_address: str = None) -> str:
    """Attempt to get the local network-connected IP address.

    Args:
        ip_address: Either desired ip address or string or "auto"

    Returns:
        Current IP address as string

    """
    if ip_address is None or ip_address.lower() == "auto":
        logger.debug("Attempting to get IP address automatically")

        hostname = socket.gethostname()
        try:
            ip_address = socket.gethostbyname(hostname)
        except socket.gaierror:
            ip_address = "unknown"

        # Workaround for Linux returning localhost
        # See: SO question #166506 by @UnkwnTech
        if ip_address in ["127.0.1.1", "127.0.0.1", "localhost", "unknown"]:
            tempsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            tempsock.connect(("8.8.8.8", 0))
            ip_address = tempsock.getsockname()[0]
            tempsock.close()

    logger.debug(f"Using IP address: {ip_address}")
    return ip_address


def make_serial(name: str) -> str:
    """Create a persistent UUID from the device name.

    Returns a suitable UUID derived from `name`. Should remain static for a
    given name.

    Args:
        name: Friendly device name (e.g. "living room light")

    Returns:
        Persistent UUID as string

    """
    return str(uuid.uuid3(uuid.NAMESPACE_X500, name))


def module_from_file(modname: str, path_str: str) -> ModuleType:
    """Load a module into `modname` from a file path.

    Args:
        modname: The desired module name
        path_str: Path to the file

    Returns:
        Module read in from path_str

    """
    path = pathlib.Path(path_str).expanduser()
    sys.path.append(str(path.parents[0]))
    spec = importlib.util.spec_from_file_location(modname, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    return module


def make_udp_sock() -> socket.socket:
    """Make a suitable udp socket to listen for device discovery requests.

    I would *love* to get rid of this function and just use the built-in
    options to `create_datagram_endpoint` (e.g. `allow_broadcast` with
    appropriate local and remote addresses), but having no luck. Would be
    thrilled if someone can figure this out in a better way than this or
    <https://github.com/n8henrie/fauxmo/blob/c5419b3f61311e5386387e136d26dd8d4a55518c/src/fauxmo/protocols.py#L149>.

    Returns:
        Socket suitable for responding to multicast requests

    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    reuseport = getattr(socket, "SO_REUSEPORT", None)
    if reuseport:
        sock.setsockopt(socket.SOL_SOCKET, reuseport, 1)

    sock.bind(("", 1900))

    group = socket.inet_aton("239.255.255.250")
    mreq = struct.pack("4sL", group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    return sock


def get_unused_port() -> int:
    """Temporarily binds a socket to an unused system assigned port.

    Returns:
        Port number

    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("", 0))
        port = sock.getsockname()[1]
        return port
