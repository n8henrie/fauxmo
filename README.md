# fauxmo

Python 3 module that emulates Belkin WeMo devices for use with the Amazon Echo.

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

1. `cp config-sample.json config.json`
1. Edit config.json
1. `python3 fauxmo.py [-v]`
1. Have the Echo "find connected devices"
1. Test: "Alexa turn on [the kitchen light]"

Currently all the code is in `fauxmo.py`, but I hope to refactor it into a
module soon. It has an example REST handler class that reacts to on
and off commands using the
[python-requests](http://docs.python-requests.org/en/latest/) library as well
as a handler for the [Home Assistant Python
API](https://home-assistant.io/developers/python_api); these are examples of a
multitude of ways that you could have the Echo trigger an action.

**Note:** unless you specify port numbers in the creation of your fauxmo
objetcs, your virtual switch devices will use a different port every time you
run fauxmo.py, which will make it hard for the Echo to find them. So you should
plan to either leave the script running for long periods or choose fixed port
numbers.

Once fauxmo.py is running, simply tell your Echo to "find connected devices" or
open a browser to or your mobile device to the [connected home
settings](http://alexa.amazon.com/#settings/connected-home) page and `Discover
devices`

## Reading list:

- <http://www.makermusings.com/2015/07/13/amazon-echo-and-home-automation>
- <http://www.makermusings.com/2015/07/18/virtual-wemo-code-for-amazon-echo>
- <http://hackaday.com/2015/07/16/how-to-make-amazon-echo-control-fake-wemo-devices>
- <https://developer.amazon.com/appsandservices/solutions/alexa/alexa-skills-kit>
- <https://en.wikipedia.org/wiki/Universal_Plug_and_Play>
- <http://www.makermusings.com/2015/07/19/home-automation-with-amazon-echo-apps-part-1>
- <http://www.makermusings.com/2015/08/22/home-automation-with-amazon-echo-apps-part-2>
