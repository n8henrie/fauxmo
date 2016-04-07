import pytest
from fauxmo import fauxmo
import threading
from time import sleep
import http.server
import json
import socketserver

@pytest.fixture(scope="session")
def fauxmo_server():
    server = threading.Thread(target=fauxmo.main,
                             kwargs={'config_path': "tests/test_config.json"},
                             daemon=True)
    server.start()
    sleep(1)
    return


@pytest.fixture(scope="session")
def fake_switch_one():
    with open('tests/test_config.json') as f:
        config = json.load(f)
    port = 12345

    Handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("localhost", 2345), Handler)
    httpd_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    httpd_thread.start()
    return
