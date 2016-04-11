# Changelog

Will not contain minor changes -- feel free to look through `git log` for
more detail.

## 0.3.0 :: 20160409

- Fauxmo now uses asyncio and requires Python >= 3.4.4
- *Extensive* changes to codebase
- Handler classes renamed for PEP8 (capitalization)
- Moved some general purpose functions to `fauxmo.utils` module
- Both the UDP and TCP servers are now in `fauxmo.protocols`
- Added some rudimentary [pytest](http://pytest.org/latest) tests including [tox](http://tox.readthedocs.org/en/latest) and [Travis](https://travis-ci.org/) support
- Updated documentation on several classes

## 0.2.0 :: 20160324

- Add additional HTTP verbs and options to `RestApiHandler` and Indigo sample
  to config
    - **NB:** Breaking change: `json` config variable now needs to be either
      `on_json` or `off_json`
- Make `RestApiHandler` DRYer with `functools.partialmethod`
- Add `SO_REUSEPORT` to `upnp.py` to make life easier on OS X

## 0.1.11 :: 20160129

- Consolidate logger to `__init__.py` and import from there in other modules

## 0.1.8 :: 20160129

- Add the ability to manually specify the host IP address for cases when the
  auto detection isn't working (https://github.com/n8henrie/fauxmo/issues/1)
- Deprecated the `DEBUG` setting in `config.json`. Just use `-vvv` from now on.

## 0.1.6 :: 20160105

- Fix for Linux not returning local IP
    - restored method I had removed from Maker Musings original / pre-fork
      version not knowing it would introduce a bug where Linux returned
      127.0.1.1 as local IP address

## 0.1.4 :: 20150104

- Fix default verbosity bug introduced in 1.1.3

## 0.1.0 :: 20151231

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
