"""conftest.py :: Setup fixtures for pytest."""

from multiprocessing import Process
from time import sleep

import httpbin
import pytest
from fauxmo import fauxmo


@pytest.fixture(scope="session")
def fauxmo_server():
    config_path = "tests/test_config.json"
    server = Process(target=fauxmo.main,
                     kwargs={'config_path': config_path},
                     daemon=True)

    fauxmo_device = Process(target=httpbin.core.app.run,
                            kwargs={"host": "127.0.0.1", "port": 8000},
                            daemon=True)

    server.start()
    fauxmo_device.start()
    sleep(1)

    yield

    fauxmo_device.terminate()
    fauxmo_device.join()

    server.terminate()
    server.join()
