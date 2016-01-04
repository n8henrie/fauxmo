# Changelog

Will not contain minor changes -- feel free to look through `git log` for
more detail.

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
