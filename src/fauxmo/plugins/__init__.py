"""fauxmo.plugins :: Provide ABC for Fauxmo plugins."""

import abc
from typing import Callable


class FauxmoPlugin(abc.ABC):
    """Provide ABC for Fauxmo plugins.

    This will become the `plugin` attribute of a `Fauxmo` instance. Its `on`
    and `off` methods will be called when Alexa turns something `on` or `off`.

    All keys (other than the list of `DEVICES`) from the config will be passed
    into FauxmoPlugin as kwargs at initialization, which should let users do
    some interesting things. However, that means users employing custom config
    keys will need to override `__init__` and either set the `name` and
    "private" `_port` attributes manually or pass the appropriate args to
    `super().__init__()`.
    """

    def __init__(self, *, name: str, port: int) -> None:
        """Initialize FauxmoPlugin.

        Keyword Args:
            name: Required, device name
            port: Required, port that the Fauxmo associated with this plugin
                  should run on

        Note about `port`: if not given in config, it will be set to an
        apparently free port in `fauxmo.fauxmo` before FauxmoPlugin
        initialization. This attribute serves no default purpose in the
        FauxmoPlugin but is passed in to be accessible by user code (i.e. for
        logging / debugging). Alternatively, one could accept and throw away
        the passed in `port` value and generate their own port in a plugin,
        since the Fauxmo device determines its port from the plugin's instance
        attribute.

        The `_latest_action` attribute stores the most recent successful
        action, which is set by the `__getattribute__` hackery for successful
        `.on()` and `.off()` commands.

        """
        self._name = name
        self._port = port
        self._latest_action = "off"

    def __getattribute__(self, name: str) -> Callable:
        """Intercept `.on()` and `.off()` to set `_latest_action` attribute."""
        if name in ["on", "off"]:
            success = object.__getattribute__(self, name)()
            if success is True:
                self._latest_action = name
            return lambda: success
        else:
            return object.__getattribute__(self, name)

    @property
    def port(self) -> int:
        """Return port attribute in read-only manner."""
        return self._port

    @property
    def name(self) -> str:
        """Return name attribute in read-only manner."""
        return self._name

    @abc.abstractmethod
    def on(self) -> bool:
        """Run function when Alexa turns this Fauxmo device on."""
        pass

    @abc.abstractmethod
    def off(self) -> bool:
        """Run function when Alexa turns this Fauxmo device off."""
        pass

    @abc.abstractmethod
    def get_state(self) -> str:
        """Run function when Alexa requests device state.

        Should return "on" or "off" if it can be determined, or "unknown" if
        there is no mechanism for determining the device state, in which case
        Alexa will complain that the device is not responding.

        If state cannot be determined, a plugin can opt into this
        implementation, which falls back on the `_latest_action` attribute.
        It is intentionally left as an abstract method so that plugins cannot
        omit a `get_state` method completely, which could lead to unexpected
        behavior; instead, they should explicitly `return super().get_state()`.
        """
        return self.latest_action

    def close(self) -> None:
        """Run when shutting down; allows plugin to clean up state."""
        pass

    @property
    def latest_action(self) -> str:
        """Return latest action in read-only manner.

        Must be a function instead of e.g. property because it overrides
        `get_state`, and therefore must be callable.

        """
        return self._latest_action

    def __repr__(self) -> str:
        """Provide a default human-readable representation of the plugin."""
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({attrs})"
