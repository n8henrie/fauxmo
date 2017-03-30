# Fauxmo README

[![Build
Status](https://travis-ci.org/n8henrie/fauxmo.svg?branch=master)](https://travis-ci.org/n8henrie/fauxmo)

Python 3 module that emulates Belkin WeMo devices for use with the Amazon Echo.

Originally forked from <https://github.com/makermusings/fauxmo>, unforked to
enable GitHub code search (which currently doesn't work in a fork), and because
the libraries have diverged substantially.

- Documentation: [fauxmo.readthedocs.org](https://fauxmo.readthedocs.org)

## Introduction

The Amazon Echo is able to control certain types of home automation devices by
voice. Fauxmo provides emulated Belkin Wemo devices that the Echo can turn on
and off by voice, locally, and with minimal lag time. Currently these Fauxmo
devices can be configured to make requests to an HTTP server or to a [Home
Assistant](https://home-assistant.io) instance via [its Python
API](https://home-assistant.io/developers/python_api/) and only require a JSON
config file for setup.

As of version v0.4.0, Fauxmo uses several API features and f-strings that
require Python 3.6+. I highly recommend looking into
[pyenv](https://github.com/pyenv/pyenv) if you're currently on an older Python
version and willing to upgrade. Otherwise, check out the FAQ section at the
bottom for tips on installing an older Fauxmo version (though note that I will
not be continuing development or support for older versions).

## Usage

Installation into a venv is *highly recommended*, especially since it's baked
into the recent Python versions that Fauxmo requires.

### Simple install: From PyPI

1. `python3 -m venv venv`
1. `source venv/bin/activate`
1. `python3 -m pip install fauxmo`
1. Make a `config.json` based on
   [`config-sample.json`](https://github.com/n8henrie/fauxmo/blob/master/config-sample.json)
1. `fauxmo -c config.json [-v]`

### Simple install of dev branch from GitHub (for testing features in
development -- for actually contributing to development clone the repo as per
below)

1. `python3 -m venv venv`
1. `source venv/bin/activate`
1. `pip install [-e] git+https://github.com/n8henrie/fauxmo.git@dev`

### Install for development from GitHub

1. `git clone https://github.com/n8henrie/fauxmo.git`
1. `cd fauxmo`
1. `python3 -m venv venv`
1. `source venv/bin/activate`
1. `pip install -e .[dev]`
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

NB: As discussed in [#20](https://github.com/n8henrie/fauxmo/issues/20), the
example files in `extras/` are *not* included when you install from PyPI\*
(using `pip`). If you want to use them, you either need to clone the repo or
you can download them individually using tools like `wget` or `curl` by
navigating to the file in your web browser, clicking the `Raw` button, and
using the resulting URL in your address bar.

\* As of Fauxmo v0.4.0 `extras/` has been added to `MANIFEST.in` and may be
included somewhere depending on installation from the `.tar.gz` vs `whl`
format -- if you can't find them, you should probably just get the files
manually as described above.

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

## Plugins

Plugins are small user-extendible classes that allow users to easily make their
own actions for Fauxmo to run by way of Alexa commands. They were previously
called Handlers and may be referred to as such in places in the code and
documentation.

Fauxmo v0.4.0 implements a new and breaking change in the way Handlers were
implemented in previous versions, which requires modification of the
`config.json` file (as described below).

A few plugins and the ABC from which the plugins are required to inherit are
included and installed by default in the `fauxmo.plugins` package. The
pre-installed plugins, like the rest of the core Fauxmo code, have no third
party dependencies.

The pre-installed plugins include

- `fauxmo.plugins.simplehttpplugin.SimpleHTTPPlugin`
- `fauxmo.plugins.command_line.CommandLinePlugin`

`SimpleHTTPPlugin` responds to Alexa's `on` and `off` commands by making
requests to URL endpoints by way of
[`urllib`](https://docs.python.org/3/library/urllib.html). Example uses cases
relevant to the IOT community might be a Flask server served from localhost
that provides a nice web interface for toggling switches, whose endpoints could
be added as the `on_cmd` and `off_cmd` args to a `SimpleHTTPPlugin` instance
to allow activation by way of Alexa -> Fauxmo.

Please see details regarding `SimpleHTTPPlugin` configuration in the class's
docstring, which I intend to continue as a convention for Fauxmo plugins.
Users hoping to make more complicated requests may be interested in looking at
`RESTAPIPlugin` in the
[`fauxmo-plugins repository`](https://github.com/n8henrie/fauxmo-plugins),
which uses Requests for a much friendlier API.

Users can easily create their own plugins, which is the motivation behind most
of the changes in Fauxmo v0.4.0.

To get started:

1. Decide on a name for your plugin class. I highly recommend something
   descriptive, CamelCase and a `Plugin` suffix, e.g. `FooSwitcherPlugin`.
1. I strongly recommend naming your module the same as the plugin, but in all
   lower case, e.g. `fooswitcherplugin.py`.
1. Note the path to your plugin, which will need to be included in your
   `config.json` as `path` (absolute path recommended, `~` for homedir is okay)
1. Write your class, which should at minimum:
    - inherit from `fauxmo.plugins.FauxmoPlugin`
    - provide the methods `on()` and `off()`
1. Any required settings will be read from your `config.json` and passed into
   your plugin as kwargs at initialization, see below.

In addition to the above, if you intend to share your plugin with others, I
strongly recommend that you:

- include generous documentation as a module level docstring
- note specific versions of any dependencies in that docstring
  - Because these user plugins are kind of "side-loaded," you will need to
    install their dependencies into the appropriate environment manually, so
    it's important to let other users know exactly what versions you use.

### Notable Fauxmo plugins

Please see <https://github.com/n8henrie/fauxmo-plugins>, where user
contributions of interesting plugins are more than welcome!

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
    - `plugin`: Dictionary for `RESTAPIHandler` configuration
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

## Security considerations

Because Fauxmo v0.4.0+ loads any user plugin specified in their config, it will
run untested and potentially unsafe code. If an intruder were to have write
access to your `config.json`, they could cause you all kinds of trouble. Then
again, if they already have write access to your computer, you probably have
bigger problems. Consider making your config.json `0600` for your user, or
perhaps `0644 root:YourFauxmoUser`. Use Fauxmo at your own risk, with or
without user plugins.

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
