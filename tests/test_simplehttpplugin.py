"""test_simplehttpplugin.py :: Tests for SimpleHTTPPlugin."""

import json
import typing as t

import pytest

from fauxmo.plugins.simplehttpplugin import SimpleHTTPPlugin


def test_simplehttpplugin(simplehttpplugin_target: t.Callable) -> None:
    """Test simplehttpplugin.

    Uses the fauxmo_device fixture (runs httpbin) to emulate the *target* of
    SimpleHTTPPlugin's `on_cmd` and `off_cmd`, ensures these run and return
    200, which should make the `.on()` and `.off()` methods return True.
    """
    with open("tests/test_config.json") as conf_file:
        config = json.load(conf_file)

    for device_conf in config["PLUGINS"]["SimpleHTTPPlugin"]["DEVICES"]:
        device = SimpleHTTPPlugin(**device_conf)
        assert device.on() is True
        assert device.off() is True

        state = device.get_state()
        if device.state_cmd is not None:
            assert state == "on"
        else:
            assert state == "unknown"

        device.close()


def test_simplehttpplugin_state(
    fauxmo_server: t.Callable, simplehttpplugin_target: t.Callable
) -> None:
    """Test simplehttpplugin's handling of state.

    Need a real server for the state tests, since the fauxmo server sets the
    `_latest_action` attribute

    """
    config_path_str = "tests/test_simplehttpplugin_config.json"

    with open(config_path_str) as conf_file:
        config = json.load(conf_file)

    for device_conf in config["PLUGINS"]["SimpleHTTPPlugin"]["DEVICES"]:
        device = SimpleHTTPPlugin(**device_conf)

        use_fake_state = device_conf.get("use_fake_state")
        initial_state = device_conf.get("initial_state")

        if use_fake_state is True:
            if initial_state is None:
                # If using fake state, user should configure an initial state
                with pytest.raises(AttributeError):
                    device.get_state()
            else:
                assert device.get_state() == initial_state

        assert device.off(), "Unable to initialize state to `off`"

        success = device.on()
        state = device.get_state()

        # Use device name as a hint for testing specific cases:
        #     - both state_response_on and state_response_off are true
        if 'should return `"unknown"`' in device.name.casefold():
            assert state == "unknown"
            continue

        # Device not configured to get state
        if device.state_cmd is None and use_fake_state is not True:
            assert state == "unknown"

        # Either state_cmd is implemented or use_fake_state is True, either
        # way `success` should indicate whether it worked
        elif success:
            assert state == "on"
        else:
            assert state == "off"

        success = device.off()
        state = device.get_state()

        # Device not configured to get state
        if device.state_cmd is None and use_fake_state is not True:
            assert state == "unknown"

        # If `.off()` didn't succeed it's unknown whether the device will
        # be on or off, based on success of `.on()`, so only test for case
        # of success.
        elif success:
            assert state == "off"
