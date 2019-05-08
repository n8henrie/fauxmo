"""conftest.py :: Setup fixtures for pytest."""

import json
import socket
import time
from multiprocessing import Process
from typing import Iterator

import httpbin
import pytest
from fauxmo import fauxmo


@pytest.fixture(scope="session")
def fauxmo_server() -> Iterator:
    """Create a Fauxmo server from test_config.json."""
    config_path_str = "tests/test_config.json"
    server = Process(
        target=fauxmo.main,
        kwargs={"config_path_str": config_path_str},
        daemon=True,
    )

    server.start()

    # Make sure the server is up and running before proceeding with more tests
    with open("tests/test_config.json") as f:
        config = json.load(f)
    ip_address = config["FAUXMO"]["ip_address"]

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.connect((ip_address, 1900))

        for retry in range(10):
            try:
                sock.sendall(b'"ssdp:discover" urn:Belkin:device:**')
                sock.settimeout(0.1)
                data = sock.recv(4096)
            except (ConnectionError, socket.timeout):
                time.sleep(0.1)
                continue
            else:
                if b"Fauxmo" not in data:
                    continue
                break

    yield

    server.terminate()
    server.join()


@pytest.fixture(scope="session")
def simplehttpplugin_target() -> Iterator:
    """Simulate the endpoints triggered by RESTAPIPlugin."""
    httpbin_address = ("127.0.0.1", 8000)
    fauxmo_device = Process(
        target=httpbin.core.app.run,
        kwargs={
            "host": httpbin_address[0],
            "port": httpbin_address[1],
            "threaded": True,
        },
        daemon=True,
    )

    fauxmo_device.start()

    for retry in range(10):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            errno = sock.connect_ex(httpbin_address)

            # Returns 0 if connect was successful
            if errno:
                time.sleep(0.1)
                continue

            sock.sendall(b"GET / HTTP/1.0\r\n")
            sock.shutdown(socket.SHUT_WR)
            data = sock.recv(15)
            if data != "HTTP/1.0 200 OK":
                continue
            break

    yield

    fauxmo_device.terminate()
    fauxmo_device.join()
