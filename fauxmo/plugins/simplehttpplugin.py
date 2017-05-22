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
from functools import partialmethod  # type: ignore # not yet in typeshed
from http.cookiejar import CookieJar

from fauxmo.plugins import FauxmoPlugin


class SimpleHTTPPlugin(FauxmoPlugin):
    """Plugin for interacting with HTTP devices.

    The Fauxmo class expects plguins to be instances of objects that inherit
    from FauxmoPlugin and have on() and off() methods that return True on
    success and False otherwise. This class takes a mix of url, method, header,
    body, and auth data and makes REST calls to a device.
    """

    def __init__(self, *, name: str, port: int, on_cmd: str, off_cmd: str,
                 method: str = "GET", on_data: dict = None,
                 off_data: dict = None, headers: dict = None, user: str = None,
                 password: str = None) -> None:
        """Initialize a SimpleHTTPPlugin instance.

        Keyword Args:
            on_cmd: URL to be called when turning device on
            off_cmd: URL to be called when turning device off
            method: HTTP method to be used for both `on()` and `off()`
            on_data: HTTP body to turn device on
            off_data: HTTP body to turn device off
            headers: Additional headers for both `on()` and `off()`
            user: Username for HTTP authentication (basic or digest only)
            password: Password for HTTP authentication (basic or digest only)
        """
        self.method = method
        self.headers = headers or {}

        self.on_cmd = on_cmd
        self.off_cmd = off_cmd

        self.on_data = on_data
        self.off_data = off_data

        if user and password:
            manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
            manager.add_password(None, (on_cmd, off_cmd), user, password)

            jar = CookieJar()
            cookie_handler = urllib.request.HTTPCookieProcessor(jar)

            # Will get a mypy error here until
            # https://github.com/python/typeshed/pull/1082 gets synced into
            # mypy and a new mypy release comes out
            basic_handler = urllib.request.HTTPBasicAuthHandler(manager)  # type: ignore # noqa
            digest_handler = urllib.request.HTTPDigestAuthHandler(manager)  # type: ignore # noqa

            opener = urllib.request.build_opener(basic_handler, digest_handler,
                                                 cookie_handler)
            self.urlopen = opener.open
        else:
            self.urlopen = urllib.request.urlopen

        super().__init__(name=name, port=port)

    def set_state(self, cmd: str, data: str) -> bool:
        """Call HTTP method, for use by `functools.partialmethod`.

        Args:
            cmd: Either `"on_cmd"` or `"off_cmd"`, for `getattr(self, cmd)`
            data: Either `"on_data"` or `"off_data"`, for `getattr(self, data)`

        Returns:
            Boolean indicating whether it state was set successfully

        """
        # `data` is passed in as either `"on_data"` or `"off_data"` as string,
        # so `getattr` to get the actual content as dict. Same for `cmd`.
        data_dict = getattr(self, data)
        if data_dict:
            data_bytes = urllib.parse.urlencode(data_dict).encode('utf8')
        else:
            data_bytes = None
        req = urllib.request.Request(
            url=getattr(self, cmd),
            data=data_bytes,
            headers=self.headers,
            method=self.method
        )

        with self.urlopen(req) as resp:
            if isinstance(resp, http.client.HTTPResponse):
                return resp.status in (200, 201)
            return False

    on = partialmethod(set_state, 'on_cmd', 'on_data')
    off = partialmethod(set_state, 'off_cmd', 'off_data')
