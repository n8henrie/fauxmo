"""conftest.py :: Setup fixtures for pytest."""

import socket
import time
from multiprocessing import Process
from types import TracebackType
from typing import Callable, Iterator, Optional, Type

import httpbin
import pytest

from fauxmo import fauxmo
from fauxmo.utils import get_local_ip


class TestFauxmoServer:
    """Runs Fauxmo in a separate thread."""

    def __init__(self, config_path_str: str) -> None:
        """Initialize test Fauxmo server with path to config."""
        self.config_path_str = config_path_str

    def __enter__(self) -> str:
        """Start a TextFauxmoServer, returns the ip address it's running on."""
        self.server = Process(
            target=fauxmo.main,
            kwargs={"config_path_str": self.config_path_str},
            daemon=True,
        )
        self.server.start()
        local_ip = None
        while local_ip is None:
            local_ip = get_local_ip()
        return get_local_ip()

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[Exception],
        traceback: Optional[TracebackType],
    ) -> None:
        """Terminate the server and join the thread on exit."""
        self.server.terminate()
        self.server.join()


@pytest.fixture(scope="session")
def fauxmo_server() -> Callable[[str], TestFauxmoServer]:
    """Use a pytest fixture to provide the TestFauxmoServer context manager."""
    return TestFauxmoServer


@pytest.fixture(scope="session")
def simplehttpplugin_target() -> Iterator:
    """Simulate the endpoints triggered by SimpleHTTPPlugin."""
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
