"""test_fauxmo.py :: Tests for `fauxmo` package."""

import socket
import typing as t
import xml.etree.ElementTree as ET  # noqa

import pytest
import requests

from fauxmo import fauxmo
from fauxmo.protocols import Fauxmo
from fauxmo.utils import get_unused_port


def test_udp_search(fauxmo_server: t.Callable) -> None:
    """Test device search request to UPnP / SSDP server."""
    msg = b'MAN: "ssdp:discover"' + b"ST: urn:Belkin:device:**"
    addr = ("239.255.255.250", 1900)

    with fauxmo_server("tests/test_config.json"):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            reuseport = getattr(socket, "SO_REUSEPORT", None)
            if reuseport:
                sock.setsockopt(socket.SOL_SOCKET, reuseport, 1)

            sock.sendto(msg, addr)
            data = sock.recv(4096)

    assert b"LOCATION: http://" in data
    assert b"/setup.xml" in data


def test_setup(fauxmo_server: t.Callable) -> None:
    """Test TCP server's `/setup.xml` endpoint."""
    with fauxmo_server("tests/test_config.json") as fauxmo_ip:
        resp = requests.get(f"http://{fauxmo_ip}:12345/setup.xml")
    assert resp.status_code == 200

    root = ET.fromstring(resp.text)

    assert (
        root.find(".//friendlyName").text == "fake switch one"  # type: ignore
    )


def test_turnon(
    fauxmo_server: t.Callable, simplehttpplugin_target: t.Callable
) -> None:
    """Test TCP server's "on" action for SimpleHTTPPlugin."""
    data = (
        b'SOAPACTION: "urn:Belkin:service:basicevent:1#SetBinaryState"'
        b"<BinaryState>1</BinaryState>"
    )

    with fauxmo_server("tests/test_config.json") as fauxmo_ip:
        resp = requests.post(
            f"http://{fauxmo_ip}:12345/upnp/control/basicevent1", data=data
        )
    assert resp.status_code == 200


def test_getbinarystate(
    fauxmo_server: t.Callable, simplehttpplugin_target: t.Callable
) -> None:
    """Test TCP server's "GetBinaryState" action for SimpleHTTPPlugin."""
    data = b'Soapaction: "urn:Belkin:service:basicevent:1#GetBinaryState"'

    with fauxmo_server("tests/test_config.json") as fauxmo_ip:
        resp = requests.post(
            f"http://{fauxmo_ip}:12345/upnp/control/basicevent1", data=data
        )
    assert resp.status_code == 200

    root = ET.fromstring(resp.text)
    val = root.find(".//BinaryState").text  # type: ignore
    assert val in ["0", "1"]


def test_getfriendlyname(
    fauxmo_server: t.Callable, simplehttpplugin_target: t.Callable
) -> None:
    """Test TCP server's "GetFriendlyName" action for SimpleHTTPPlugin."""
    data = b'soapaction: "urn:Belkin:service:basicevent:1#GetFriendlyName"'

    with fauxmo_server("tests/test_config.json") as fauxmo_ip:
        resp = requests.post(
            f"http://{fauxmo_ip}:12345/upnp/control/basicevent1", data=data
        )
    assert resp.status_code == 200

    root = ET.fromstring(resp.text)
    assert (
        root.find(".//FriendlyName").text == "fake switch one"  # type: ignore
    )


def test_old_config_fails() -> None:
    """Ensure the config for fauxmo < v0.4.0 fails with SystemExit."""
    with pytest.raises(SystemExit):
        fauxmo.main(config_path_str="tests/old-config-sample.json")


def test_content_length() -> None:
    """Test `CONTENT-LENGTH` HTTP header with non-ascii characters.

    https://github.com/n8henrie/fauxmo/issues/70

    """
    assert "CONTENT-LENGTH: 3" in Fauxmo.add_http_headers("foo")
    assert "CONTENT-LENGTH: 4" in Fauxmo.add_http_headers("föo")


def test_get_unused_port() -> None:
    """
    Test get_unused_port function in utils.py.

    Checks to make sure the port returned by the function is actually available
    after function is run.
    Also ensures a socket can be successfully created with the given port.

    """
    available_port = get_unused_port()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("", available_port))
        assert int(sock.getsockname()[1]) == available_port
