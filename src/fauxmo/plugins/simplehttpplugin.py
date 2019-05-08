"""simplehttpplugin.py :: Fauxmo plugin for simple HTTP requests.

Fauxmo plugin that makes simple HTTP requests in its `on` and `off` methods.
Comes pre-installed in Fauxmo as an example for user plugins.

For more complicated requests (e.g. authentication, sending JSON), check out
RESTAPIPlugin in `https://github.com/n8henrie/fauxmo-plugins/`, which takes
advantage of Requests' rich API.
"""

import http
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from typing import Mapping, Union

from fauxmo.plugins import FauxmoPlugin


class SimpleHTTPPlugin(FauxmoPlugin):
    """Plugin for interacting with HTTP devices.

    The Fauxmo class expects plguins to be instances of objects that inherit
    from FauxmoPlugin and have on() and off() methods that return True on
    success and False otherwise. This class takes a mix of url, method, header,
    body, and auth data and makes REST calls to a device.

    This is probably less flexible than using Requests but doesn't add any
    non-stdlib dependencies. For an example using Requests, see the
    fauxmo-plugins repo.

    The implementation of the `get_state()` method is admittedly sloppy, trying
    to be somewhat generic to cover a broad range of devices that may have
    a state that can be queried by either GET or POST request (sometimes
    differing from the method required to turn on or off), and whose response
    often contains the state. For example, if state is returned by a GET
    request to `localhost:8765/state` with `<p>Device is running</p>` or
    `<p>Device is not running</p>`, you could use those strings as
    `state_command_on` and `state_command_off`, respectively.
    """

    def __init__(
        self,
        *,
        headers: dict = None,
        method: str = "GET",
        name: str,
        off_cmd: str,
        off_data: Union[Mapping, str] = None,
        on_cmd: str,
        on_data: Union[Mapping, str] = None,
        state_cmd: str = None,
        state_data: Union[Mapping, str] = None,
        state_method: str = "GET",
        state_response_off: str = None,
        state_response_on: str = None,
        password: str = None,
        port: int,
        user: str = None,
    ) -> None:
        """Initialize a SimpleHTTPPlugin instance.

        Keyword Args:
            headers: Additional headers for both `on()` and `off()`
            method: HTTP method to be used for both `on()` and `off()`
            name: Name of the device
            off_cmd: URL to be called when turning device off
            off_data: Optional POST data to turn device off
            on_cmd: URL to be called when turning device on
            on_data: Optional POST data to turn device on
            state_cmd: URL to be called to determine device state
            state_data: Optional POST data to query device state
            state_method: HTTP method to be used for `get_state()`
            state_response_off: If this string is in the response to state_cmd,
                                the device is off.
            state_response_on: If this string is in the response to state_cmd,
                               the device is on.
            password: Password for HTTP authentication (basic or digest only)
            port: Port that this device will run on
            user: Username for HTTP authentication (basic or digest only)
        """
        self.method = method
        self.state_method = state_method
        self.headers = headers or {}

        self.on_cmd = on_cmd
        self.off_cmd = off_cmd
        self.state_cmd = state_cmd

        self.on_data = self._to_bytes(on_data)
        self.off_data = self._to_bytes(off_data)
        self.state_data = self._to_bytes(state_data)

        self.state_response_on = state_response_on
        self.state_response_off = state_response_off

        if user and password:
            manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
            manager.add_password(None, (on_cmd, off_cmd), user, password)

            jar = CookieJar()
            cookie_handler = urllib.request.HTTPCookieProcessor(jar)

            basic_handler = urllib.request.HTTPBasicAuthHandler(manager)
            digest_handler = urllib.request.HTTPDigestAuthHandler(manager)

            opener = urllib.request.build_opener(
                basic_handler, digest_handler, cookie_handler
            )
            self.urlopen = opener.open
        else:
            self.urlopen = urllib.request.urlopen

        super().__init__(name=name, port=port)

    @staticmethod
    def _to_bytes(data: Union[Mapping, str]) -> bytes:
        if isinstance(data, Mapping):
            data = urllib.parse.urlencode(data)
        if isinstance(data, str):
            return data.encode("utf8")
        return data

    def set_state(self, cmd: str, data: bytes) -> bool:
        """Call HTTP method, for use by `functools.partialmethod`.

        Args:
            cmd: Either `"on_cmd"` or `"off_cmd"`, for `getattr(self, cmd)`
            data: Either `"on_data"` or `"off_data"`, for `getattr(self, data)`

        Returns:
            Boolean indicating whether it state was set successfully

        """
        req = urllib.request.Request(
            url=cmd, data=data, headers=self.headers, method=self.method
        )

        with self.urlopen(req) as resp:
            if isinstance(resp, http.client.HTTPResponse):
                return resp.status in (200, 201)
        return False

    def on(self) -> bool:
        """Turn device on by calling `self.on_cmd` with `self.on_data`.

        Returns:
            True if the request seems to have been sent successfully

        """
        return self.set_state(self.on_cmd, self.on_data)

    def off(self) -> bool:
        """Turn device off by calling `self.off_cmd` with `self.off_data`.

        Returns:
            True if the request seems to have been sent successfully

        """
        return self.set_state(self.off_cmd, self.off_data)

    def get_state(self) -> str:
        """Get device state.

        Returns:
            "on", "off", or "unknown"

        """
        if self.state_cmd is None:
            return "unknown"

        req = urllib.request.Request(
            url=self.state_cmd,
            data=self.state_data,
            headers=self.headers,
            method=self.state_method,
        )

        with self.urlopen(req) as resp:
            response_content = resp.read().decode("utf8")

        if self.state_response_off in response_content:
            return "off"
        elif self.state_response_on in response_content:
            return "on"
        return "unknown"
