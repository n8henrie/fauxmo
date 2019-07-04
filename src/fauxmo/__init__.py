"""fauxmo :: Emulated Belkin Wemo devices for use with the Amazon Echo."""

import logging
import logging.handlers

__author__ = "Nathan Henrie"
__email__ = "nate@n8henrie.com"
__version__ = "v0.4.9"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s:%(lineno)-8d %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("fauxmo")
syslog_handler = logging.handlers.SysLogHandler()
logger.addHandler(syslog_handler)
