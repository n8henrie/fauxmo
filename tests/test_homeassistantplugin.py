"""test_homeassistantplugin :: Tests for Fauxmo's `HomeAssistantPlugin`."""


import json
from http.client import HTTPResponse
from unittest.mock import MagicMock, patch

from fauxmo.plugins.homeassistantplugin import HomeAssistantPlugin

config_path_str = "tests/test_homeassistantplugin_config.json"


@patch("urllib.request.urlopen")
def test_homeassistantplugin(mock: MagicMock) -> None:
    """Ensure a reasonable HomeAssistant REST endpoint is called."""
    with open(config_path_str) as f:
        config = json.load(f)

    response = MagicMock(spec=HTTPResponse)
    response.status = 200
    response.read.return_value = b'{"state": "off"}'
    mock.return_value.__enter__.return_value = response

    plugin_vars = {
        k: v
        for k, v in config["PLUGINS"]["HomeAssistantPlugin"].items()
        if k not in {"DEVICES", "path"}
    }
    for device_conf in config["PLUGINS"]["HomeAssistantPlugin"]["DEVICES"]:
        device = HomeAssistantPlugin(**{**plugin_vars, **device_conf})

        specified_domain = device_conf.get("domain")
        if specified_domain:
            assert device.domain == specified_domain
        else:
            assert device.domain == device.entity_id.split(".")[0]

        signal = HomeAssistantPlugin.service_map[device.domain.lower()]["on"]
        assert device.on() is True
        req = mock.call_args[0][0]
        assert req.full_url == (
            f"http://localhost:8123/api/services/{device.domain}/{signal}"
        )
        assert (
            req.data.decode()
            == f'{{"entity_id": "{device_conf["entity_id"]}"}}'
        )
        assert req.headers == {
            "Authorization": "Bearer abc123",
            "Content-type": "application/json",
        }
        assert int(req.host.rsplit(":")[-1]) == plugin_vars["ha_port"]
        assert req.get_method() == "POST"

        signal = HomeAssistantPlugin.service_map[device.domain.lower()]["off"]
        assert device.off() is True
        req = mock.call_args[0][0]
        assert req.full_url == (
            f"http://localhost:8123/api/services/{device.domain}/{signal}"
        )
        assert (
            req.data.decode()
            == f'{{"entity_id": "{device_conf["entity_id"]}"}}'
        )
        assert req.headers == {
            "Authorization": "Bearer abc123",
            "Content-type": "application/json",
        }
        assert int(req.host.rsplit(":")[-1]) == plugin_vars["ha_port"]
        assert req.get_method() == "POST"

        assert device.get_state() == "off"
        req = mock.call_args[0][0]
        assert (
            req.full_url
            == f"http://localhost:8123/api/states/{device_conf['entity_id']}"
        )
        assert req.data is None
        assert req.headers == {
            "Authorization": "Bearer abc123",
            "Content-type": "application/json",
        }
        assert int(req.host.rsplit(":")[-1]) == plugin_vars["ha_port"]
        assert req.get_method() == "GET"
