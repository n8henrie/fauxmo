# Changelog

Will not contain minor changes -- feel free to look through `git log` for
more detail.

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
