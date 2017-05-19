"""conftest.py :: Setup fixtures for pytest."""

from multiprocessing import Process
from time import sleep
from typing import Generator

from fauxmo import fauxmo

import httpbin
import pytest


@pytest.fixture(scope="session")
def fauxmo_server() -> Generator:
    """Create a Fauxmo server from test_config.json."""
    config_path_str = "tests/test_config.json"
    server = Process(target=fauxmo.main,
                     kwargs={'config_path_str': config_path_str},
                     daemon=True)

    server.start()
    sleep(1)

    yield

    # Time to finish a request in process
    sleep(0.1)
    server.terminate()
    server.join()


@pytest.fixture(scope="function")
def simplehttpplugin_target() -> Generator:
    """Simulates the endpoints triggered by RESTAPIPlugin."""
    fauxmo_device = Process(target=httpbin.core.app.run,
                            kwargs={"host": "127.0.0.1", "port": 8000},
                            daemon=True)

    fauxmo_device.start()
    sleep(1)

    yield

    # Time to finish a request in process
    sleep(0.1)
    fauxmo_device.terminate()
    fauxmo_device.join()
