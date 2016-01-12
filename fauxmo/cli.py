"""cli.py
Argparse based CLI for fauxmo. Helps provide console_script via argparse. Also
initializes logging.
"""

import argparse
import sys
from .fauxmo import main
import logging
import logging.handlers


def cli():
    """Parse command line options, provide entry point for console scripts"""

    arguments = sys.argv[1:]
    parser = argparse.ArgumentParser(description="Emulate Belkin Wemo devices "
                                     "for use with Amaazon Echo")
    parser.add_argument("-v", "--verbose", help="increase verbosity (may "
                        "repeat up to -vv)", action="count", default=1)
    parser.add_argument("-c", "--config", help="specify alternate config file")
    args = parser.parse_args(arguments)

    logging.basicConfig(
            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
            )

    logger = logging.getLogger("fauxmo")
    handler = logging.handlers.SysLogHandler()
    logger.addHandler(handler)

    # args.verbose defaults to 1 -> 30 == logging.WARNING
    verbosity = max(40 - 10 * args.verbose, 10)
    logger.setLevel(verbosity)

    main(config_path=args.config, verbosity=verbosity)

if __name__ == "__main__":
    cli()
