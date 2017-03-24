"""test_fauxmo.py :: Tests for `fauxmo` package."""

import json
import socket
import xml.etree.ElementTree as etree

from fauxmo.plugins.simplehttphandler import SimpleHTTPHandler

import pytest
import requests


def test_udp_search(fauxmo_server: pytest.fixture) -> None:
    """Test device search request to UPnP / SSDP server"""

    msg = b'"ssdp:discover"' + b'urn:Belkin:device:**'
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1)
    sock.sendto(msg, ('localhost', 1900))
    data = sock.recv(4096)

    assert b'LOCATION: http://' in data
    assert b'/setup.xml' in data


def test_setup(fauxmo_server: pytest.fixture) -> None:
    """Test TCP server's `/setup.xml` endpoint"""

    r = requests.get('http://127.0.0.1:12345/setup.xml')
    assert r.status_code == 200

    root = etree.fromstring(r.text)
    assert root.find(".//friendlyName").text == 'fake switch one'


def test_turnon(fauxmo_server: pytest.fixture) -> None:
    """Test TCP server's "on" action for SimpleHTTPHandler"""

    data = '<BinaryState>1</BinaryState>'

    # requests.exceptions.Timeout suggests it was able to issue the request to
    # Fauxmo without exception, but there aren't any devices running at the
    # configured `on_cmd` address (probably should be true)
    resp = requests.post('http://127.0.0.1:12345/upnp/control/basicevent1',
                         data=data)
    assert resp.status_code == 200


def test_simplehttphandler(fauxmo_server: pytest.fixture) -> None:
    with open("tests/test_config.json") as f:
        config = json.load(f)

    for device in config["PLUGINS"]["SimpleHTTPHandler"]["DEVICES"]:
        print(device)
        assert SimpleHTTPHandler(**device).on() is True
        assert SimpleHTTPHandler(**device).off() is True
