# [Changelog](https://keepachangelog.com)

Will not contain minor changes -- feel free to look through `git log` for
more detail.

## v0.4.9 :: 20190527

- Add py37 support (including Travis workaround)
- Fix bug in content-length calculation (thanks @tim15)
- Replace `find_unused_port` with local function (thanks @schneideradam)
- Use black for formatting
- Update `config-sample.txt` for changes in [HomeAssistant
  API](https://developers.home-assistant.io/docs/en/external_api_rest.html)

## v0.4.8 :: 20180804

- Add `.close()` method to `FauxmoPlugin`s, allowing for cleanup (thanks
  [@howdypierce](https://github.com/howdypierce))
  [discussion](https://github.com/n8henrie/fauxmo/issues/58), e907245
- Append plugins directory to `sys.path` for more convenient loading of
  additional modules (thanks [@howdypierce](https://github.com/howdypierce))
  [discussion](https://github.com/n8henrie/fauxmo/issues/58), 03f2101
- Add HTTP headers to `/eventservice.xml` and `/metainfoservice.xml` endpoints
  5a53268

## v0.4.7 :: 20180512

- Minor dev-side changes
    - Use pipenv for dev dependency management
- Add utf-8 to readme parsing (5 days ago) (thanks
     [@hestela](https://github.com/n8henrie/fauxmo/commits?author=hestela)!)
     49d2c57
- Change newline to `\r\n` in HTTP responses (thanks
   [@GlennPegden2](https://github.com/GlennPegden2)) 239bc79
- Match `MAN:` case insensitive (thanks [@wingett](https://github.com/wingett))
  8307096
- Add GetBinaryState and GetFriendlyName commands including test cases (thanks
  [@howdypierce](https://github.com/howdypierce)!) 71392de
- Make comparison of the "SOAPACTION" header case-insensitive, per UPnP spec
  (thanks [@howdypierce](https://github.com/howdypierce)!) a5cdf82
- Add fallback for determining IP address when DNS resolution is a problem
  (thanks [@howdypierce](https://github.com/howdypierce)!) c2d7f13
- Bugfix: ~/.fauxmo/ not being read as a location for config file (thanks
  [@howdypierce](https://github.com/howdypierce)!) c322c9b

## v0.4.6 :: 20180212

- Mostly changes to try to fix compatibility with newer generation Echos / Echo
  Plus, see #38

## v0.4.5 :: 20171114

- Support new GetBinaryState command (fixes n8henrie/fauxmo#31)

## v0.4.3 :: 20170914

- Add `--version` to cli
- Add `python_requires` specifier to `setup.py`
- Bind to specific address in `make_udp_sock` (`fauxmo.utils`), seems to fix
  some intermittent failing tests on MacOS.

## v0.4.2 :: 20170601

- Add additional linters to tests
- Set reuseaddr and reuseport before binding socket

## v0.4.0 :: 20170402

- Rename handlers to plugins
- Add interface for user plugins
- Add type hints
- Require Python 3.6
- Eliminate third party dependencies
- Make sure to close connection when plugin commands fail / return False

## v0.3.3 :: 20160722

- Added compatibility for `rollershutter` to `handlers.hass`
- Changed `handlers.hass` to send values from a dict to make addition of new
  services easier in the future

## v0.3.2 :: 20160419

- Update SSDPServer to `setsockopt` to permit receiving multicast broadcasts
- `sock` kwarg to `create_datagram_endpoint` no longer necessary, restoring
  functionality to Python 3.4.0 - 3.4.3 (closes #6)
- `make_udp_sock()` no longer necessary, removed from `fauxmo.utils`
- Tox and Travis configs switched to use Python 3.4.2 instead of 3.4.4 (since
  3.4.2 is the latest available in the default Raspbian Jessie repos)

## v0.3.1 :: 20160415

- Don't decode the UDP multicast broadcasts (hopefully fixes #7)
    - They might not be from the Echo and might cause a `UnicodeDecodeError`
    - Just search the bytes instead
- Tests updated for this minor change

## v0.3.0 :: 20160409

- Fauxmo now uses asyncio and requires Python >= 3.4.4
- *Extensive* changes to codebase
- Handler classes renamed for PEP8 (capitalization)
- Moved some general purpose functions to `fauxmo.utils` module
- Both the UDP and TCP servers are now in `fauxmo.protocols`
- Added some rudimentary [pytest](http://pytest.org/latest) tests including [tox](http://tox.readthedocs.org/en/latest) and [Travis](https://travis-ci.org/) support
- Updated documentation on several classes

## v0.2.0 :: 20160324

- Add additional HTTP verbs and options to `RestApiHandler` and Indigo sample
  to config
    - **NB:** Breaking change: `json` config variable now needs to be either
      `on_json` or `off_json`
- Make `RestApiHandler` DRYer with `functools.partialmethod`
- Add `SO_REUSEPORT` to `upnp.py` to make life easier on OS X

## v0.1.11 :: 20160129

- Consolidate logger to `__init__.py` and import from there in other modules

## v0.1.8 :: 20160129

- Add the ability to manually specify the host IP address for cases when the
  auto detection isn't working (https://github.com/n8henrie/fauxmo/issues/1)
- Deprecated the `DEBUG` setting in `config.json`. Just use `-vvv` from now on.

## v0.1.6 :: 20160105

- Fix for Linux not returning local IP
    - restored method I had removed from Maker Musings original / pre-fork
      version not knowing it would introduce a bug where Linux returned
      127.0.1.1 as local IP address

## v0.1.4 :: 20150104

- Fix default verbosity bug introduced in 1.1.3

## v0.1.0 :: 20151231

- Continue to convert to python3 code
- Pulled in a few PRs by [@DoWhileGeek](https://github.com/DoWhileGeek) working
towards python3 compatibility and improved devices naming with dictionary
- Renamed a fair number of classes
- Added kwargs to several class and function calls for clarity
- Renamed several variables for clarity
- Got rid of a few empty methods
- Import devices from `config.json` and include a sample
- Support `POST`, headers, and json data in the RestApiHandler
- Change old debug function to use logging module
- Got rid of some unused dependencies
- Moved license (MIT) info to LICENSE
- Added argparse for future console scripts entry point
- Added Home Assistant API handler class
- Use "string".format() instead of percent
- Lots of other minor refactoring
