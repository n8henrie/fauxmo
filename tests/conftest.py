"""conftest.py :: Setup fixtures for pytest."""

from __future__ import annotations

import json
import socket
import time
from multiprocessing import Process
from threading import Thread
from types import TracebackType
from typing import Callable, Iterator, Type

import httpbin
import pytest

from fauxmo import fauxmo
from fauxmo.utils import get_local_ip


class TestFauxmoServer:
    """Runs Fauxmo in a separate thread.

    A Process is used instead of a thread since there is no way to terminate a
    server thread (which runs forever), so it is difficult to start and
    terminate examples with different configurations.
    """

    def __init__(self, config_path_str: str) -> None:
        """Initialize test Fauxmo server with path to config."""
        self.config_path_str = config_path_str
        with open(config_path_str) as f:
            config = json.load(f)
        first_plugin = [*config["PLUGINS"].values()][0]
        self.first_port = first_plugin["DEVICES"][0]["port"]

    def __enter__(self) -> str:
        """Start a TextFauxmoServer, returns the ip address it's running on."""
        self.server = Process(
            target=fauxmo.main,
            kwargs={"config_path_str": self.config_path_str},
        )
        self.server.start()

        local_ip = get_local_ip()
        for _retry in range(10):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect((local_ip, self.first_port))
            except ConnectionRefusedError:
                time.sleep(0.1)
                continue
            break

        return local_ip

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_value: Exception | None,
        traceback: TracebackType | None,
    ) -> None:
        """Terminate the server and join the thread on exit."""
        self.server.terminate()
        self.server.join()


@pytest.fixture(scope="function")
def fauxmo_server() -> Callable[[str], TestFauxmoServer]:
    """Use a pytest fixture to provide the TestFauxmoServer context manager."""
    return TestFauxmoServer


@pytest.fixture(scope="session")
def simplehttpplugin_target() -> Iterator:
    """Simulate the endpoints triggered by SimpleHTTPPlugin."""
    httpbin_address = ("127.0.0.1", 8000)
    fauxmo_device = Thread(
        target=httpbin.core.app.run,
        kwargs={
            "host": httpbin_address[0],
            "port": httpbin_address[1],
            "threaded": True,
            "debug": False,
        },
        daemon=True,
    )

    fauxmo_device.start()

    for _retry in range(10):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(httpbin_address)
        except ConnectionRefusedError:
            time.sleep(0.1)
            continue
        break
    yield
