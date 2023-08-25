# Fauxmo README

master: [![master branch build status](https://github.com/n8henrie/fauxmo/actions/workflows/python-package.yml/badge.svg?branch=master)](https://github.com/n8henrie/fauxmo/actions/workflows/python-package.yml)
dev: [![dev branch build status](https://github.com/n8henrie/fauxmo/actions/workflows/python-package.yml/badge.svg?branch=dev)](https://github.com/n8henrie/fauxmo/actions/workflows/python-package.yml)

Python 3 module that emulates Belkin WeMo devices for use with the Amazon Echo.

Originally forked from <https://github.com/makermusings/fauxmo>, unforked to
enable GitHub code search (which currently doesn't work in a fork), and because
the libraries have diverged substantially.

- Documentation: [fauxmo.readthedocs.org](https://fauxmo.readthedocs.org)

## Introduction

The Amazon Echo is able to control certain types of home automation devices by
voice. Fauxmo provides emulated Belkin Wemo devices that the Echo can turn on
and off by voice, locally, and with minimal lag time. Currently these Fauxmo
devices can be configured to make requests to an HTTP server such as [Home
Assistant](https://home-assistant.io) or to run other commands locally on the
device and only require a JSON config file for setup.

As of version v0.4.0, Fauxmo uses several API features and f-strings that
require Python 3.6+. I highly recommend looking into
[pyenv](https://github.com/pyenv/pyenv) if you're currently on an older Python
version and willing to upgrade. Otherwise, check out the FAQ section at the
bottom for tips on installing an older Fauxmo version (though note that I will
not be continuing development or support for older versions).

For what it's worth, if you're concerned about installing pyenv on a
low-resource machine like the Raspberry Pi, I encourage you to [review my
notes](https://n8henrie.com/2018/02/pyenv-size-and-python-36-speed-installation-time-on-raspberry-pi/)
on the size and time required to install Python 3.6 with pyenv on a Raspberry
Pi and the nontrivial improvement in speed (with a simple pystone benchmark)
using an optimized pyenv-installed 3.6 as compared to the default Raspbian
3.5.3.

## Terminology

faux (`\ˈfō\`): imitation

WeMo: Belkin home automation product with which the Amazon Echo can interface

Fauxmo (`\ˈfō-mō\`): Python 3 module that emulates Belkin WeMo devices for use
with the Amazon Echo.

Fauxmo has a server component that helps register "devices" with the Echo (which
may be referred to as the Fauxmo server or Fauxmo core). These devices are then
exposed individually, each requiring its own port, and may be referred to as a
Fauxmo device or a Fauxmo instance. The Echo interacts with each Fauxmo device
as if it were a separate WeMo device.

## Usage

Installation into a venv is *highly recommended*, especially since it's baked
into the recent Python versions that Fauxmo requires.

Additionally, please ensure you're using a recent version of pip (>= 9.0.1)
prior to installation: `pip install --upgrade pip`

### Simple install: From PyPI

1. `python3 -m venv .venv`
1. `source ./.venv/bin/activate`
1. `python3 -m pip install fauxmo`
1. Make a `config.json` based on
   [`config-sample.json`][config-sample.json]
1. `fauxmo -c config.json [-v]`

As of `v0.6.0`, you can *optionally* install `uvloop` for potentially better
performance, which *might* be helpful if you have a large number of devices or
a network with lots of broadcast mdns traffic. If it is present, `fauxmo` will
take advantage. It is not terribly difficult to install `uvloop` but you are on
your own: <https://github.com/MagicStack/uvloop>.

### Simple install of dev branch from GitHub

This is a good strategy for testing features in development -- for actually
contributing to development, clone the repo as per below)

1. `python3 -m venv .venv`
1. `source ./.venv/bin/activate`
1. `pip install [-e] git+https://github.com/n8henrie/fauxmo.git@dev`

### Install for development from GitHub

1. `git clone https://github.com/n8henrie/fauxmo.git`
1. `cd fauxmo`
1. `python3 -m venv .venv`
1. `source ./.venv/bin/activate`
1. `pip install -e .[dev,test]`
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

### Set Fauxmo to run automatically in the background

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

A few plugins and the ABC from which the plugins are required to inherit may
be included and installed by default in the `fauxmo.plugins` package. Any
pre-installed plugins, like the rest of the core Fauxmo code, have no third
party dependencies.

So far, the pre-installed plugins include:

- [`fauxmo.plugins.simplehttpplugin.SimpleHTTPPlugin`](https://github.com/n8henrie/fauxmo/blob/master/src/fauxmo/plugins/simplehttpplugin.py)
- [`fauxmo.plugins.commandlineplugin.CommandLinePlugin`](https://github.com/n8henrie/fauxmo/blob/master/src/fauxmo/plugins/commandlineplugin.py)
- [`fauxmo.plugins.homeassistantplugin.HomeAssistantPlugin`](https://github.com/n8henrie/fauxmo/blob/master/src/fauxmo/plugins/homeassistantplugin.py)

`SimpleHTTPPlugin` responds to Alexa's `on` and `off` commands by making
requests to URL endpoints by way of
[`urllib`](https://docs.python.org/3/library/urllib.html). Example uses cases
relevant to the IOT community might be a Flask server served from localhost
that provides a nice web interface for toggling switches, whose endpoints could
be added as the `on_cmd` and `off_cmd` args to a `SimpleHTTPPlugin` instance
to allow activation by way of Alexa -> Fauxmo.

As of Fauxmo v0.4.5, the `FauxmoPlugin` abstract base class (and therefore all
derivate Fauxmo plugins) requires a `get_state` method, which tells Alexa a
device's state. If you don't have a way to determine devices state, you can
just have your `get_state` method return `"unknown"`, but please review the
notes on `get_state` below.

Also, see details regarding plugin configuration in each class's docstring,
which I intend to continue as a convention for Fauxmo plugins. Users hoping to
make more complicated requests may be interested in looking at `RESTAPIPlugin`
in the [`fauxmo-plugins
repository`](https://github.com/n8henrie/fauxmo-plugins), which uses Requests
for a much friendlier API.

### User plugins

Users can easily create their own plugins, which is the motivation behind most
of the changes in Fauxmo v0.4.0.

To get started:

1. Decide on a name for your plugin class. I highly recommend something
   descriptive, CamelCase and a `Plugin` suffix, e.g. `FooSwitcherPlugin`.
1. I strongly recommend naming your module the same as the plugin, but in all
   lower case, e.g. `fooswitcherplugin.py`.
1. Note the path to your plugin, which will need to be included in your
   `config.json` as `path` (absolute path recommended, `~` for homedir is
   okay).
1. Write your class, which must at minimum:
    - inherit from `fauxmo.plugins.FauxmoPlugin`.
    - provide the methods `on()`, `off()`, and `get_state()`.
        - Please note that unless the Echo has a way to determine the device
          state, it will likely respond that your "device is not responding"
          after you turn a device on (or in some cases off, or both), but it
          should still be able to switch the device.
        - If you want to ignore the actual device's state and just return the
          last successful action as the current state (e.g. if `device.on()`
          succeeded then return `"on"`), your plugin can return
          `super().get_state()` as its `get_state()` method. Some of the
          included plugins can be configured to have this behavior using a
          `use_fake_state` flag in their configuration (please look at the
          documentation and source code of the plugins for further details).
          Note that this means it won't update to reflect state changes that
          occur outside of Fauxmo (e.g. manually flipping a switch, or toggling
          with a different program), whereas a proper `get_state`
          implementation may be able to do so.
        - If using fake state or if your device cannot readily report its state
          upon request (for example if you poll for state with a background
          process like mqtt), you should also set an `initial_state` in your
          config. As of August 2023, prior to adding a newly discovered device,
          Alexa requests its state and will fail to add the device if it can't
          report a state.

1. Any required settings will be read from your `config.json` and passed into
   your plugin as kwargs at initialization, see below.

In addition to the above, if you intend to share your plugin with others, I
strongly recommend that you:

- Include generous documentation as a module level docstring.
- Note specific versions of any dependencies in that docstring.
  - Because these user plugins are kind of "side-loaded," you will need to
    manually install their dependencies into the appropriate environment, so
    it's important to let other users know exactly what versions you use.

Be aware, when fauxmo loads a plugin, it will add the directory
containing the plugin to the Python path, so any other Python modules in this
directory might be loaded by unscrupulous code. This behavior was adopted in
part to facilitate installing any plugin dependencies in a way that will be
available for import (e.g. `cd "$MYPLUGINPATH"; pip install -t $MYPLUGINDEPS`).

### Notable plugin examples

NB: You may need to *manually* install additional dependencies for these to
work -- look for the dependencies in the module level docstring.

- <https://github.com/n8henrie/fauxmo-plugins>
    - `RESTAPIPlugin`
        - Trigger HTTP requests with your Echo.
        - Similar to `SimpleHTTPPlugin`, but uses
          [Requests](https://github.com/kennethreitz/requests) for a simpler
          API and easier modification.
    - `MQTTPlugin`
        - Trigger MQTT events with your Echo
    - User contributions of interesting plugins are more than welcome!

## Configuration

I recommend that you copy and modify
[`config-sample.json`](https://github.com/n8henrie/fauxmo/blob/master/config-sample.json).
Fauxmo will use whatever config file you specify with `-c` or will search for
`config.json` in the current directory, `~/.config/fauxmo`, `~/.fauxmo/`, and
`/etc/fauxmo/` (in that order). The minimal configuration settings are:

- `FAUXMO`: General Fauxmo settings
    - `ip_address`: Optional[str] - Manually set the server's IP address.
      Recommended value: `"auto"`.
- `PLUGINS`: Top level key for your plugins, values should be a dictionary of
  (likely CamelCase) class names, spelled identically to the plugin class, with
  each plugin's settings as a subdictionary.
    - `ExamplePlugin`: Your plugin class name here, case sensitive.
        - `path`: The absolute path to the Python file in which the plugin
          class is defined (please see the section on user plugins above).
          Required for user plugins / plugins not pre-installed in the
          `fauxmo.plugins` subpackage.
        - `example_var1`: For convenience and to avoid redundancy, your plugin
          class can *optionally* use config variables at this level that
          will be shared for all `DEVICES` listed in the next section (e.g. an
          API key that would be shared for all devices of this plugin type).
          If provided, your plugin class must consume this variable in a custom
          `__init__`.
        - `DEVICES`: List of devices that will employ `ExamplePlugin`
            - `name`: Optional[str] -- Name for this device. Optional in the
              sense that you can leave it out of the config as long as you set
              it in your plugin code as the `_name` attribute, but it does need
              to be set somewhere. If you omit it from config you will also
              need to override the `__init__` method, which expects a `name`
              kwarg.
            - `port`: Optional[int] -- Port that Echo will use connect to
              device. Should be different for each device, Fauxmo will attempt
              to set automatically if absent from config. NB: Like `name`, you
              can choose to set manually in your plugin code by overriding the
              `_port` attribute (and the `__init__` method, which expects a
              `port` kwarg otherwise).
            - `example_var2`: Config variables for individual Fauxmo devices
              can go here if needed (e.g. the URL that should be triggered when
              a device is activated). Again, your plugin class will need to
              consume them in a custom `__init__`.


Each user plugin should describe its required configuration in its module-level
docstring. The only required config variables for all plugins is `DEVICES`,
which is a `List[dict]` of configuration variables for each device of that
plugin type. Under `DEVICES` it is a good idea to set a fixed, high, free
`port` for each device, but if you don't set one, Fauxmo will try to pick a
reasonable port automatically (though it will change for each run).

Please see [`config-sample.json`][config-sample.json] for a more concrete idea
of the structure of the config file, using the built-in `SimpleHTTPPlugin` for
demonstration purposes. Below is a description of the kwargs that
`SimpleHTTPPlugin` accepts.

- `name`: What you want to call the device (how to activate by
  Echo)
- `port`: Port the Fauxmo device will run on
- `on_cmd`: str -- URL that should be requested to turn device on.
- `off_cmd`: str -- URL that should be requested to turn device off.
- `state_cmd`: str -- URL that should be requested to query device state
- `method` / `state_method`: Optional[str] = GET -- GET, POST, PUT, etc.
- `headers`: Optional[dict]  -- Extra headers
- `on_data` / `off_data` / `state_data`: Optional[dict] -- POST data
- `state_response_on` / `state_response_off`: str -- If this string is in
  contained in the response from `state_cmd`, then the devices is `on` or
  `off`, respectively
- `user` / `password`: Optional[str] -- Enables HTTP authentication (basic or
  digest only)
- `use_fake_state`: Optional[bool] -- If `True`, override the plugin's
  `get_state` method to return the latest successful action as the device
  state. NB: The proper json boolean value for Python's `True` is `true`, not
  `True` or `"true"`.

## Security

I am not a technology professional and make no promises regarding the security
of this software. Specifically, plugins such as `CommandLinePlugin` execute
arbitrary code from your configuration without any validation. If your
configuration can be tampered with, you're in for a bad time.

That said, if your configuration can be tampered with (i.e. someone already has
write access on your machine), then you likely have bigger problems.

Regardless, a few reasonable precautions that I recommend:

- run `fauxmo` in a virtulaenv, even without any dependencies
- run `fauxmo` as a dedicated unprivileged user with its own group
- remove write access from the `fauxmo` user and group for your config file and
  any plugin files (perhaps `chmod 0640 config.json; chown me:fauxmo
  config.json`)
- consider using a firewall like `ufw`, but don't forget that you'll need to
  open up ports for upnp (`1900`, UDP) and ports for all your devices that
  you've configured (in `config.json`).

For example, if I had 4 echo devices at 192.168.1.5, 192.168.1.10,
192.168.1.15, and 192.168.1.20, and Fauxmo was configured with devices at each
of port 12345-12350, to configure `ufw` I might run something like:

```console
$ for ip in 5 10 15 20; do
    sudo ufw allow \
        from 192.168.1."$ip" \
        to any \
        port 1900 \
        proto udp \
        comment "fauxmo upnp"
    sudo ufw allow \
        from 192.168.1."$ip" \
        to any \
        port 12345:12350 \
        proto tcp \
        comment "fauxmo devices"
done
```

You use Fauxmo at your own risk, with or without user plugins.

## Troubleshooting / FAQ

Your first step in troubleshooting should probably be to "forget all devices"
(which as been removed from the iOS app but is still available at
[alexa.amazon.com](https://alexa.amazon.com)), re-discover devices, and make
sure to refresh your device list (e.g. pull down on the "devices" tab in the
iOS app, or just close out the app completely and re-open).

- How can I increase my logging verbosity?
    - `-v[vv]`
    - `-vv` (`logging.INFO`) is a good place to start when debugging
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
- Does Fauxmo work with non-Echo emulators like Alexa AVS or Echoism.io?
    - [Apparently not.](https://github.com/n8henrie/fauxmo/issues/22)
- How do I find my Echo firmware version?
    - https://alexa.amazon.com -> Settings -> [Device Name] -> Device Software Version

### Installing Python 3.10 with [pyenv](https://github.com/pyenv/pyenv)

```bash
sudo install -o $(whoami) -g $(whoami) -d /opt/pyenv
git clone https://github.com/pyenv/pyenv /opt/pyenv
cat <<'EOF' >> ~/.bashrc
export PYENV_ROOT="/opt/pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
EOF
source ~/.bashrc
pyenv install 3.10.6
```

You can then install Fauxmo into Python 3.10 in a few ways, including:

```bash
# Install with pip
"$(pyenv root)"/versions/3.10.6/bin/python3.10 -m pip install fauxmo

# Show full path to Fauxmo console script
pyenv which fauxmo

# Run with included console script
fauxmo -c /path/to/config.json -vvv

# I recommend using the full path for use in start scripts (e.g. systemd, cron)
"$(pyenv root)"/versions/3.10.6/bin/fauxmo -c /path/to/config.json -vvv

# Alternatively, this also works (after `pip install`)
"$(pyenv root)"/versions/3.10.6/bin/python3.10 -m fauxmo.cli -c config.json -vvv
```

## Docker (alpha)

I'm not a heavy docker user, but I thought it might be helpful to also provide
a docker image.

The Dockerfile can be run locally from a copy of the repo; you'll obviously
need to change `config-sample.json` to an absolute path to your `config.json`.

```bash
$ docker run --network=host --rm -it \
    -v $(pwd)/config-sample.json:/etc/fauxmo/config.json:ro \
    "$(docker build -q .)"
```

As far as I'm aware the `network=host` will be unavoidable due to the need to
listen (and respond) to UPnP broadcasts.

## Buy Me a Coffee

[☕️](https://n8henrie.com/donate)

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
- [https://www.rilhia.com/tutorials/using-upnp-enabled-devices-talend-belkin-wemo-switch](https://web.archive.org/web/20160419092252/https://www.rilhia.com/tutorials/using-upnp-enabled-devices-talend-belkin-wemo-switch)

[config-sample.json]: https://github.com/n8henrie/fauxmo/blob/master/config-sample.json
