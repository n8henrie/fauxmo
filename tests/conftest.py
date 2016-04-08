import pytest
from fauxmo import fauxmo
from multiprocessing import Process
from time import sleep


@pytest.yield_fixture(scope="session")
def fauxmo_server():
    server = Process(target=fauxmo.main,
                     kwargs={'config_path': "tests/test_config.json"},
                     daemon=True)
    server.start()
    sleep(1)
    yield
    server.terminate()
    server.join()
