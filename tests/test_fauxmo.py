"""test_fauxmo.py
Tests for `fauxmo` module.
"""

import pytest
import fauxmo.fauxmo
import requests
import xml.etree.ElementTree as etree

def test_setup(fauxmo_server):

    r = requests.get('http://localhost:12345/setup.xml')
    assert r.status_code == 200

    root = etree.fromstring(r.text)
    assert root.find(".//friendlyName").text == 'fake switch one'


def test_turnon(fauxmo_server, fake_switch_one):
    headers = {'SOAPACTION':
               '"urn:Belkin:service:basicevent:1#SetBinaryState"'}
    payload = '<BinaryState>1</BinaryState>'

    r = requests.get('http://localhost:12345', headers=headers, data=payload)
    # assert r.status_code == 200
