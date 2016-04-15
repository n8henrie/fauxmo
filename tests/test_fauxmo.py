"""test_fauxmo.py

Tests for `fauxmo` module.
"""

import requests
import xml.etree.ElementTree as etree
import pytest
import socket


def test_udp_search(fauxmo_server):
    """Test device search request to UPnP / SSDP server"""

    msg = b'"ssdp:discover"' + b'urn:Belkin:device:**'
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1)
    sock.sendto(msg, ('localhost', 1900))
    data = sock.recv(4096)

    assert b'LOCATION: http://localhost:12345/setup.xml' in data


def test_setup(fauxmo_server):
    """Test TCP server's `/setup.xml` endpoint"""

    r = requests.get('http://localhost:12345/setup.xml')
    assert r.status_code == 200

    root = etree.fromstring(r.text)
    assert root.find(".//friendlyName").text == 'fake switch one'


def test_turnon(fauxmo_server):
    """Test TCP server's "on" action for RESTAPIHandler"""

    data = '<BinaryState>1</BinaryState>'

    # requests.exceptions.Timeout suggests it was able to issue the request to
    # Fauxmo without exception, but there aren't any devices running at the
    # configured `on_cmd` address (probably should be true)
    with pytest.raises(requests.exceptions.Timeout):
        requests.post('http://127.0.0.1:12345/upnp/control/basicevent1',
                      data=data, timeout=1)
