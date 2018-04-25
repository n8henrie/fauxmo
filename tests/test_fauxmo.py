"""test_fauxmo.py :: Tests for `fauxmo` package."""

import json
import socket
import xml.etree.ElementTree as etree

import pytest
import requests
from fauxmo import fauxmo
from fauxmo.plugins.simplehttpplugin import SimpleHTTPPlugin


def test_udp_search(fauxmo_server: pytest.fixture) -> None:
    """Test device search request to UPnP / SSDP server."""
    msg = b'MAN: "ssdp:discover"' + b'ST: urn:Belkin:device:**'
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    reuseport = getattr(socket, "SO_REUSEPORT", None)
    if reuseport:
        sock.setsockopt(socket.SOL_SOCKET, reuseport, 1)

    sock.settimeout(0.1)

    addr = ("239.255.255.250", 1900)
    sock.sendto(msg, addr)
    data = sock.recv(4096)

    assert b'LOCATION: http://' in data
    assert b'/setup.xml' in data


def test_setup(fauxmo_server: pytest.fixture) -> None:
    """Test TCP server's `/setup.xml` endpoint."""
    resp = requests.get('http://127.0.0.1:12345/setup.xml')
    assert resp.status_code == 200

    root = etree.fromstring(resp.text)
    assert root.find(".//friendlyName").text == 'fake switch one'


def test_turnon(fauxmo_server: pytest.fixture,
                simplehttpplugin_target: pytest.fixture) -> None:
    """Test TCP server's "on" action for SimpleHTTPPlugin."""
    data = (b'SOAPACTION: "urn:Belkin:service:basicevent:1#SetBinaryState"'
            b'<BinaryState>1</BinaryState>')

    resp = requests.post('http://127.0.0.1:12345/upnp/control/basicevent1',
                         data=data)
    assert resp.status_code == 200


def test_getbinarystate(fauxmo_server: pytest.fixture,
                simplehttpplugin_target: pytest.fixture) -> None:
    """Test TCP server's "GetBinaryState" action for SimpleHTTPPlugin."""
    data = (b'Soapaction: "urn:Belkin:service:basicevent:1#GetBinaryState"')

    resp = requests.post('http://127.0.0.1:12345/upnp/control/basicevent1',
                         data=data)
    assert resp.status_code == 200

    root = etree.fromstring(resp.text)
    val = root.find(".//BinaryState").text
    assert val in ["0", "1"]


def test_getfriendlyname(fauxmo_server: pytest.fixture,
                simplehttpplugin_target: pytest.fixture) -> None:
    """Test TCP server's "GetFriendlyName" action for SimpleHTTPPlugin."""
    data = (b'soapaction: "urn:Belkin:service:basicevent:1#GetFriendlyName"')

    resp = requests.post('http://127.0.0.1:12345/upnp/control/basicevent1',
                         data=data)
    assert resp.status_code == 200

    root = etree.fromstring(resp.text)
    assert root.find(".//FriendlyName").text == 'fake switch one'


def test_old_config_fails() -> None:
    """Ensure the config for fauxmo < v0.4.0 fails with SystemExit."""
    with pytest.raises(SystemExit):
        fauxmo.main(config_path_str="tests/old-config-sample.json")


def test_simplehttpplugin(simplehttpplugin_target: pytest.fixture) -> None:
    """Test simplehttpplugin.

    Uses the fauxmo_device fixture (runs httpbin) to emulate the *target* of
    SimpleHTTPPlugin's `on_cmd` and `off_cmd`, ensures these run and return
    200, which should make the `.on()` and `.off()` methods return True.
    """
    with open("tests/test_config.json") as conf_file:
        config = json.load(conf_file)

    for device_conf in config["PLUGINS"]["SimpleHTTPPlugin"]["DEVICES"]:
        device = SimpleHTTPPlugin(**device_conf)
        assert device.on() is True
        assert device.off() is True

        state = device.get_state()
        if device.state_cmd is not None:
            assert state == "on"
        else:
            assert state == "unknown"
