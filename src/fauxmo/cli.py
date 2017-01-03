"""cli.py
Argparse based CLI for fauxmo. Helps provide console_script via argparse. Also
initializes logging.
"""

import argparse
import sys
from .fauxmo import main
from . import logger


def cli():
    """Parse command line options, provide entry point for console scripts"""

    arguments = sys.argv[1:]
    parser = argparse.ArgumentParser(description="Emulate Belkin Wemo devices "
                                     "for use with Amaazon Echo")
    parser.add_argument("-v", "--verbose", help="increase verbosity (may "
                        "repeat up to -vvv)", action="count", default=0)
    parser.add_argument("-c", "--config", help="specify alternate config file")
    args = parser.parse_args(arguments)

    # args.verbose defaults to 0
    # 40 - 10 * 0 = 40 == logging.ERROR
    verbosity = max(40 - 10 * args.verbose, 10)
    logger.setLevel(verbosity)

    main(config_path=args.config, verbosity=verbosity)


if __name__ == "__main__":
    cli()
