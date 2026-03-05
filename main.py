from bot import Bot
from dotenv import load_dotenv

import argparse
import logging
import colorlog

load_dotenv()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verbose", "-v", help="incrase output verbosity", action="store_true"
    )
    args = parser.parse_args()

    logger = get_logger(args.verbose)

    bot = Bot(logger)
    bot.run()


def get_logger(verbose: bool = False) -> logging.Logger:
    logger = colorlog.getLogger()
    level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(level)

    if not logger.handlers:
        handler = colorlog.StreamHandler()
        handler.setFormatter(
            colorlog.ColoredFormatter(
                "%(log_color)s%(asctime)s [%(levelname)s]: %(message)s"
            )
        )
        logger.addHandler(handler)

    return logger


if __name__ == "__main__":
    main()
