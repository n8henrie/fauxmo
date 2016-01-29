# Fauxmo README

Python 3 module that emulates Belkin WeMo devices for use with the Amazon Echo.

- Documentation: [fauxmo.readthedocs.org](https://fauxmo.readthedocs.org)

## Updates 20151231 by @n8henrie:

- see
[HISTORY.md](https://github.com/n8henrie/fauxmo/blob/master/HISTORY.md)
- All credit goes to @makermusings for [the original version
  of Fauxmo](https://github.com/makermusings/fauxmo)!
    - Also thanks to @DoWhileGeek for commits towards python 3 compatibility

## Summary

The Amazon Echo will allow you to control a limited number of home automation
devices by voice. If you want to control device types that it doesn't know
about, or perform more sophisticated actions, the Echo doesn't provide any
native options. This code emulates the Belkin WeMo devices in software,
allowing you to have it appear that any number of them are on your network and
to link their on and off actions to any code you want.

## Usage

### Simple install: From PyPI

1. `python3 -m pip install fauxmo`
1. Make a `config.json` based on
   [`config-sample.json`](https://github.com/n8henrie/fauxmo/blob/master/config-sample.json)
1. `fauxmo -c config.json [-v]`

### Install for development: From GitHub

1. `git clone https://github.com/n8henrie/fauxmo.git`
1. `cd fauxmo`
1. `python3 -m venv venv`
1. `source venv/bin/activate`
1. `pip install -e .`
1. `cp config-sample.json config.json`
1. Edit `config.json`
1. `fauxmo [-v]`

### Set up the Echo

1. Have the Echo "find connected devices"
1. Test: "Alexa turn on [the kitchen light]"

### Set fauxmo to run automatically in the background

#### systemd (e.g. Raspbian Jessie)

1. Recommended: add an unprivileged user to run Fauxmo: `sudo useradd -r
   -s /bin/false fauxmo`
    - NB: Fauxmo may require root privileges if you're using ports below 1024
1. `sudo cp extras/fauxmo.service /etc/systemd/system/fauxmo.service`
1. Edit the paths in `/etc/systemd/system/fauxmo.service`
1. `sudo systemctl enable fauxmo.service`
1. `sudo systemctl start fauxmo.service`

#### launchd (OS X)

1. `cp extras/com.n8henrie.fauxmo.plist ~/Library/LaunchAgents/com.n8henrie.fauxmo.plist`
1. Edit the paths in `~/Library/LaunchAgents/com.n8henrie.fauxmo.plist`
    - You can remove the `StandardOutPath` and `StandardErrorPath` sections if
      desired
1. `launchctl load ~/Library/LaunchAgents/com.n8henrie.fauxmo.plist`
1. `launchctl start com.n8henrie.fauxmo`

Once fauxmo.py is running, simply tell your Echo to "find connected devices" or
open a browser to or your mobile device to the [connected home
settings](http://alexa.amazon.com/#settings/connected-home) page and `Discover
devices`

## Handlers

Fauxmo has an example REST handler class that reacts to on
and off commands using the
[python-requests](http://docs.python-requests.org/en/latest/) library as well
as a handler for the [Home Assistant Python
API](https://home-assistant.io/developers/python_api); these are examples of a
multitude of ways that you could have the Echo trigger an action. In
`config-sample.json`, you'll see examples of:

- A `GET` request to a local server
- A `POST` request to the [Home Assistant REST
API](https://home-assistant.io/developers/rest_api/)
- Requests to Home Asssistant's Python API

## Configuration

I recommend that you copy and modify `config-sample.json`.

- `FAUXMO`: General Fauxmo settings
    - `ip_address`: Manually set the server's IP address. Optional. Recommended
      value: `auto`
- `DEVICES`: List of devices that will employ `RestApiHandler`
    - `port`: Port that Echo will use connect to device, should be different for
      each device
    - `handler`: Dictionary for `RestApiHandler` configuration
        - `on_cmd`: URL that should be requested to turn device on
        - `on_cmd`: URL that should be requested to turn device off
        - `method`: GET or POST
        - `headers`: Optional dict for extra headers
        - `json`: Optional dict for JSON data to POST
    - `description`: What you want to call the device (how to activate by Echo)
- `HOMEASSISTANT`: Section for [Home Assistant Python
  API](https://home-assistant.io/developers/python_api)
    - `enable`: Disable this section by omitting or setting to `false`
    - `host`: IP of host running Hass
    - `port`: Port for Hass access (default: 8123)
    - `password`: Hass API password
    - `DEVICES`: List of devices that will employ `HassApiHandler`
        - `description`: What you want to call the device (how to activate by
          Echo)
        - `port`: Port that Echo will use connect to device, should be
          different for each device
        - `entity_id`: Hass identifier used in API, one easy way to find is to
          curl and grep the REST API, eg `curl http://IP_ADDRESS/api/bootstrap
          | grep entity_id`

**NB:** unless you specify port numbers in the creation of your fauxmo
objetcs, your virtual switch devices will use a different port every time you
run fauxmo.py, which will make it hard for the Echo to find them. So you should
plan to either leave the script running for long periods or choose fixed port
numbers.

## Troubleshooting / FAQ

- Increase logging verbosity with `-v[vv]`

## Reading list:

- <http://www.makermusings.com/2015/07/13/amazon-echo-and-home-automation>
- <http://www.makermusings.com/2015/07/18/virtual-wemo-code-for-amazon-echo>
- <http://hackaday.com/2015/07/16/how-to-make-amazon-echo-control-fake-wemo-devices>
- <https://developer.amazon.com/appsandservices/solutions/alexa/alexa-skills-kit>
- <https://en.wikipedia.org/wiki/Universal_Plug_and_Play>
- <http://www.makermusings.com/2015/07/19/home-automation-with-amazon-echo-apps-part-1>
- <http://www.makermusings.com/2015/08/22/home-automation-with-amazon-echo-apps-part-2>
