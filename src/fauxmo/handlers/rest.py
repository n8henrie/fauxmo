# -*- coding: utf-8 -*-
from functools import partialmethod
import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth


class RESTAPIHandler:
    """Rest API handler class.

    The Fauxmo class expects handlers to be instances of objects that have on()
    and off() methods that return True on success and False otherwise. This
    class takes a mix of url, method, header, body, and auth data and makes
    REST calls to a device.
    """

    def __init__(self, on_cmd, off_cmd, method="GET", on_data=None,
                 off_data=None, on_json=None, off_json=None, headers=None,
                 auth_type=None, user=None, password=None):
        """Initialize a RESTAPIHandler instance

        Args:
            on_cmd (str): URL to be called when turning device on
            off_cmd (str): URL to be called when turning device off

        Kwargs:
           method (str): HTTP method to be used for both `on()` and `off()`
           on_data (dict): HTTP body to turn device on
           off_data (dict): HTTP body to turn device off
           on_json (dict): JSON body to turn device on
           off_json (dict): JSON body to turn device off
           headers (dict): Additional headers for both `on()` and `off()`
           auth_type (str): Either `basic` or `digest` if needed
           user (str): Username for `auth`
           password (str): Password for `auth`
       """

        self.method = method
        self.headers = headers
        self.auth = None

        self.on_cmd = on_cmd
        self.off_cmd = off_cmd

        self.on_data = on_data
        self.off_data = off_data

        self.on_json = on_json
        self.off_json = off_json

        if auth_type:
            if auth_type.lower() == "basic":
                self.auth = HTTPBasicAuth(user, password)

            elif auth_type.lower() == "digest":
                self.auth = HTTPDigestAuth(user, password)

    def set_state(self, cmd, data, json):
        """Call HTTP method, for use by `functools.partialmethod`."""

        r = requests.request(self.method, getattr(self, cmd),
                             data=getattr(self, data),
                             json=getattr(self, json), headers=self.headers,
                             auth=self.auth)
        return r.status_code in [200, 201]

    on = partialmethod(set_state, 'on_cmd', 'on_data', 'on_json')
    off = partialmethod(set_state, 'off_cmd', 'off_data', 'off_json')
