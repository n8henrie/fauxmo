"""Fauxmo plugin to interact with Home Assistant devices.

One simple way to find your entity_id is to use curl and pipe to grep or jq.
Note that modern versions of home-assistant require you to create and include a
long-lived access token, which you can generate in the web interface at the
`/profile` endpoint.

    curl --silent --header "Authorization: Bearer YourTokenHere" \
            http://IP:PORT/api/states | jq

NB: This is just a special case of the RESTAPIPlugin (or even SimpleHTTPPlugin,
see `config-sample.json` in the main Fauxmo repo), but it makes config
substantially easier by not having to redundantly specify headers and
endpoints.

Install to Fauxmo by downloading or cloning and including in your Fauxmo
config. One easy way to make a long-lived access token is by using the frontend
and going to the `/profile` endpoint, scroll to the bottom. Documentation on
the long-lived tokens is available at
https://developers.home-assistant.io/docs/en/auth_api.html#long-lived-access-token

Example config:
```
{
    "FAUXMO": {
        "ip_address": "auto"
    },
    "PLUGINS": {
        "HomeAssistantPlugin": {
            "ha_host": "192.168.0.50",
            "ha_port": 8123,
            "ha_protocol": "http",
            "ha_token": "abc123",
            "DEVICES": [
                {
                    "name": "example Home Assistant device 1",
                    "port": 12345,
                    "entity_id": "switch.my_fake_switch"
                },
                {
                    "name": "example Home Assistant device 2",
                    "port": 12346,
                    "entity_id": "cover.my_fake_cover"
                }
            ]
        }
    }
}
```
"""

import json
import urllib.parse
import urllib.request
from collections import defaultdict
from http.client import HTTPResponse
from typing import Dict

from fauxmo.plugins import FauxmoPlugin


class HomeAssistantPlugin(FauxmoPlugin):
    """Fauxmo plugin for HomeAssistant REST API.

    Allows users to specify Home Assistant services in their config.json and
    toggle these with the Echo.
    """

    service_map: Dict[str, Dict[str, str]] = defaultdict(
        lambda: {"on": "turn_on", "off": "turn_off"}
    )
    service_map["cover"] = {
        "on": "open_cover",
        "off": "close_cover",
        "on_state": "open",
        "off_state": "closed",
    }

    def __init__(
        self,
        name: str,
        port: int,
        entity_id: str,
        ha_host: str,
        ha_port: int = 8123,
        ha_protocol: str = "http",
        ha_token: str = None,
        domain: str = None,
    ) -> None:
        """Initialize a HomeAssistantPlugin instance.

        Args:
            entity_id: `entity_id` used by HomeAssistant
            ha_host: Host running HomeAssistant
            ha_port: Port number for HomeAssistant access
            ha_protocol: http or https
            ha_token: Long-lived HomeAssistant token
            domain: Override the domain instead of guessing from `entity_id`

        """
        self.ha_url = f"{ha_protocol}://{ha_host}:{ha_port}"

        self.entity_id = entity_id

        if domain is None:
            domain = self.entity_id.split(".")[0]
            if domain == "group":
                domain = "homeassistant"
        self.domain = domain

        self.headers = {
            "Authorization": f"Bearer {ha_token}",
            "content-type": "application/json",
        }
        super().__init__(name=name, port=port)

    def send(self, signal: str) -> bool:
        """Send `signal` as determined by service_map.

        Args:
            signal: the signal the service should recongize

        """
        url = f"{self.ha_url}/api/services/{self.domain}/{signal}"
        data = {"entity_id": self.entity_id}

        req = urllib.request.Request(
            url=url,
            headers=self.headers,
            data=json.dumps(data).encode("utf8"),
            method="POST",
        )
        with urllib.request.urlopen(req) as r:
            if isinstance(r, HTTPResponse):
                return r.status == 200
            else:
                return False

    def on(self) -> bool:
        """Turn the Home Assistant device on.

        Returns: Whether the device seems to have been turned on.
        """
        on_cmd = HomeAssistantPlugin.service_map[self.domain.lower()]["on"]
        return self.send(on_cmd)

    def off(self) -> bool:
        """Turn the Home Assistant device off.

        Returns: Whether the device seems to have been turned off.
        """
        off_cmd = HomeAssistantPlugin.service_map[self.domain.lower()]["off"]
        return self.send(off_cmd)

    def get_state(self) -> str:
        """Query the state of the Home Assistant device.

        Returns: Device state as reported by HomeAssistant
        """
        url = f"{self.ha_url}/api/states/{self.entity_id}"

        req = urllib.request.Request(url=url, headers=self.headers)
        with urllib.request.urlopen(req) as r:
            response = r.read().decode("utf")
        return json.loads(response)["state"]
