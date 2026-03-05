from bot import Bot
from dotenv import load_dotenv
from config import Config

import argparse
import logging
import colorlog

load_dotenv()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verbose", "-v", help="incrase output verbosity", action="store_true"
    )
    parser.add_argument(
        "--input", "-i", help="rally configuration file or online rally url", type=str
    )
    args = parser.parse_args()

    logger = get_logger(args.verbose)
    config = Config.from_path(args.input)

    print(config.__str__())

    bot = Bot(logger, config)
    bot.run()


def get_logger(verbose: bool = False) -> logging.Logger:
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
    main()
