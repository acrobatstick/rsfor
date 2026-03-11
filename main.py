import argparse
import logging
import sys

import colorlog
from dotenv import load_dotenv

from bot import Bot
from config import Config

load_dotenv()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", help="incrase output verbosity", action="store_true")
    parser.add_argument("--input", "-i", help="rally configuration file or online rally url", type=str)
    args = parser.parse_args()

    logger = get_logger(verbose=args.verbose)
    try:
        config = Config.from_path(args.input)
    except Exception:
        logger.exception("Error while reading config")
        return 1

    print(config)

    bot = Bot(logger, config)
    bot.run()
    return 0


def get_logger(*, verbose: bool = False) -> logging.Logger:
    logger = colorlog.getLogger("rsfor")
    level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(level)

    logger.handlers.clear()

    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s [%(levelname)s]: %(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
    )
    logger.addHandler(handler)
    return logger


if __name__ == "__main__":
    sys.exit(main())
