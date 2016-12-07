# Fauxmo README

[![Build
Status](https://travis-ci.org/n8henrie/fauxmo.svg?branch=master)](https://travis-ci.org/n8henrie/fauxmo)

Python 3 module that emulates Belkin WeMo devices for use with the Amazon Echo.

- Documentation: [fauxmo.readthedocs.org](https://fauxmo.readthedocs.org)

## Introduction

The Amazon Echo is able to control certain types of home automation devices by
voice. Fauxmo provides emulated Belkin Wemo devices that the Echo can turn on
and off by voice, locally, and with minimal lag time. Currently these Fauxmo
devices can be configured to make requests to an HTTP server or to a [Home
Assistant](https://home-assistant.io) instance via [its Python
API](https://home-assistant.io/developers/python_api/) and only require a JSON
config file for setup.

As of version 0.3.0, Fauxmo uses the new [asyncio
module](https://docs.python.org/3/library/asyncio.html#module-asyncio) and
therefore requires Python >= 3.4*. Python >= 3.5 is encouraged, in case I
decide to use the new `async` and `await` keywords in the future.

\* Fauxmo 0.3.0 required Python >= 3.4.4, but Fauxmo 0.3.2 has restored
compatibility with Python >= 3.4.0.

## Usage

### Simple install: From PyPI

1. `python3 -m pip install fauxmo`
1. Make a `config.json` based on
   [`config-sample.json`](https://github.com/n8henrie/fauxmo/blob/master/config-sample.json)
1. `fauxmo -c config.json [-v]`

### Simple install of dev branch (from GitHub)

1. `pip install [-e] git+https://github.com/n8henrie/fauxmo.git@dev`

### Install for development (from GitHub)

1. `git clone https://github.com/n8henrie/fauxmo.git`
1. `cd fauxmo`
1. `python3 -m venv venv`
1. `source venv/bin/activate`
1. `pip install -e .`
1. `cp config-sample.json config.json`
1. Edit `config.json`
1. `fauxmo [-v]`

### Set up the Echo

1. Open the Amazon Alexa webapp to the [Smart
   Home](http://alexa.amazon.com/#smart-home) page
1. **With Fauxmo running**, click "Discover devices" (or tell Alexa to "find
   connected devices")
1. Ensure that your Fauxmo devices were discovered and appear with their
   names in the web interface
1. Test: "Alexa, turn on [the kitchen light]"

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

## Handlers

Fauxmo has an example REST handler class that reacts to on and off commands
using the [python-requests](http://docs.python-requests.org/en/latest/) library
as well as a handler for the [Home Assistant Python
API](https://home-assistant.io/developers/python_api); these are examples of a
multitude of ways that you could have the Echo trigger an action. In
`config-sample.json`, you'll see examples of:

- A `GET` request to a local server
- A `POST` request to the [Home Assistant REST
API](https://home-assistant.io/developers/rest_api/)
- A `PUT` request to an [Indigo](https://www.indigodomo.com/) server
- Requests to [Home Asssistant's Python
  API](https://home-assistant.io/developers/python_api/)

## Configuration

I recommend that you copy and modify
[`config-sample.json`](https://github.com/n8henrie/fauxmo/blob/master/config-sample.json).
Fauxmo will use whatever config file you specify with `-c` or will search for
`config.json` in the current directory, `~/.fauxmo/`, and `/etc/fauxmo/` (in
that order).

- `FAUXMO`: General Fauxmo settings
    - `ip_address`: Manually set the server's IP address. Optional. Recommended
      value: `auto`
- `DEVICES`: List of devices that will employ `RESTAPIHandler`
    - `port`: Port that Echo will use connect to device, should be different for
      each device
    - `handler`: Dictionary for `RESTAPIHandler` configuration
        - `on_cmd`: URL that should be requested to turn device on
        - `off_cmd`: URL that should be requested to turn device off
        - `method`: GET, POST, PUT, etc.
        - `headers`: Optional dict for extra headers
        - `on_json` / `off_json`: Optional dict of JSON data
        - `on_data` / `off_data`: Optional POST data
        - `auth_type`: `basic` or `digest` authentication, optional
        - `user` / `password`: for use with `auth_type`, also optional
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

## Troubleshooting / FAQ

- How can I increase my logging verbosity?
    - `-v[vv]`
- How can I ensure my config is valid JSON?
    - `python -m json.tool < config.json`
    - Use `jsonlint` or one of numerous online tools
- How can I install an older / specific version of Fauxmo?
    - Install from a tag:
        - `pip install git+git://github.com/n8henrie/fauxmo.git@v0.1.11`
    - Install from a specific commit:
        - `pip install
          git+git://github.com/n8henrie/fauxmo.git@d877c513ad45cbbbd77b1b83e7a2f03bf0004856`
- Where can I get more information on how the Echo interacts with devices like
  Fauxmo?
    - Check out
      [`protocol_notes.md`](https://github.com/n8henrie/fauxmo/blob/master/protocol_notes.md)

### Installing Python 3.5 with pyenv

```bash
sudo install -o $(whoami) -g $(whoami) -d /opt/pyenv
git clone https://github.com/yyuu/pyenv /opt/pyenv
echo 'export PYENV_ROOT="/opt/pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
source ~/.bashrc
pyenv install 3.5.1
```

You can then install Fauxmo into Python 3.5 in a few ways, including:

```bash
# Install with pip
"$(pyenv root)"/versions/3.5.1/bin/python3.5 -m pip install fauxmo

# Run with included console script
fauxmo -c /path/to/config.json -vvv

# Show full path to fauxmo console script
pyenv which fauxmo

# I recommend using the full path for use in start scripts (e.g. systemd, cron)
"$(pyenv root)"/versions/3.5.1/bin/fauxmo -c /path/to/config.json -vvv

# Alternatively, this also works (after `pip install`)
"$(pyenv root)"/versions/3.5.1/bin/python3.5 -m fauxmo.cli -c config.json -vvv
```

## Acknowledgements / Reading List

- Tremendous thanks to @makermusings for [the original version of
  Fauxmo](https://github.com/makermusings/fauxmo)!
    - Also thanks to @DoWhileGeek for commits towards Python 3 compatibility
- <http://www.makermusings.com/2015/07/13/amazon-echo-and-home-automation>
- <http://www.makermusings.com/2015/07/18/virtual-wemo-code-for-amazon-echo>
- <http://hackaday.com/2015/07/16/how-to-make-amazon-echo-control-fake-wemo-devices>
- <https://developer.amazon.com/appsandservices/solutions/alexa/alexa-skills-kit>
- <https://en.wikipedia.org/wiki/Universal_Plug_and_Play>
- <http://www.makermusings.com/2015/07/19/home-automation-with-amazon-echo-apps-part-1>
- <http://www.makermusings.com/2015/08/22/home-automation-with-amazon-echo-apps-part-2>
