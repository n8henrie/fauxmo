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

        signal = HomeAssistantPlugin.service_map[device.domain.lower()]["on"]
        assert device.on() is True
        assert mock.call_args[0][0].full_url == (
            "http://localhost:8123/api/services/" f"{device.domain}/{signal}"
        )

        signal = HomeAssistantPlugin.service_map[device.domain.lower()]["off"]
        assert device.off() is True
        assert mock.call_args[0][0].full_url == (
            "http://localhost:8123/api/services/" f"{device.domain}/{signal}"
        )

        assert device.get_state() == "off"
        assert (
            mock.call_args[0][0].full_url
            == f"http://localhost:8123/api/states/{device_conf['entity_id']}"
        )
