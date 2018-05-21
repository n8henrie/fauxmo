"""fauxmo.plugins :: Provide ABC for Fauxmo plugins."""

import abc


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
        """
        self._name = name
        self._port = port

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
        there is no mechanism for determining the device state.
        """
        pass

    def close(self) -> None:
        """Run when shutting down; allows plugin to clean up state."""
        pass
