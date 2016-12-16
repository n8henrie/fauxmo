# -*- coding: utf-8 -*-
import homeassistant.remote
from homeassistant.const import (SERVICE_TURN_ON, SERVICE_TURN_OFF,
                                 SERVICE_OPEN_COVER, SERVICE_CLOSE_COVER)


class HassAPIHandler:
    """Handler for Home Assistant (hass) Python API.

    Allows users to specify Home Assistant services in their config.json and
    toggle these with the Echo. While this can be done with Home Assistant's
    REST API as well (example included), I find it easier to use the Python
    API.
    """

    def __init__(self, host, password, entity, port=8123):
        """Initialize a HassAPIHandler instance

        Args:
            host (str): IP address of device running Home Assistant
            password (str): Home Assistant password
            entity (str): `entity_id` used by hass, one easy way to find is to
                          curl and grep the REST API, eg:
                          `curl http://IP/api/bootstrap | grep entity_id`

        Kwargs:
            port (int): Port running hass on the host computer (default 8123)
        """

        self.host = host
        self.password = password
        self.entity = entity
        self.port = port

        self.domain = self.entity.split(".")[0]
        if self.domain == 'group':
            self.domain = 'homeassistant'
        self.api = homeassistant.remote.API(self.host, self.password,
                                            port=self.port)

        self.service_map = {
                'switch': {
                    'on': SERVICE_TURN_ON,
                    'off': SERVICE_TURN_OFF
                    },
                'homeassistant': {
                    'on': SERVICE_TURN_ON,
                    'off': SERVICE_TURN_OFF
                    },
                'cover': {
                    'on': SERVICE_OPEN_COVER,
                    'off': SERVICE_CLOSE_COVER
                    }
                }

    def send(self, signal):
        """Send a signal to the hass `call_service` function, returns True.

        The hass Python API doesn't appear to return anything with this
        function, but will raise an exception if things didn't seem to work, so
        I have it set to just return True, hoping for an exception if there was
        a problem.

        Args:
            signal (const): signal imported from homeassistant.const. I have
            imported SERVICE_TURN_ON and SERVICE_TURN_OFF, make sure you import
            any others that you need.
        """

        homeassistant.remote.call_service(self.api, self.domain, signal,
                                          {'entity_id': self.entity})
        return True

    def on(self):
        on_cmd = self.service_map[self.domain.lower()]['on']
        return self.send(on_cmd)

    def off(self):
        off_cmd = self.service_map[self.domain.lower()]['off']
        return self.send(off_cmd)
