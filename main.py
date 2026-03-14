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
    parser.add_argument("--name", "-n", help="online rally name", type=str, default="")
    parser.add_argument("--password", "-p", help="online rally password", type=str, default="")
    parser.add_argument("--dump", help="dump online rally into a yaml file", action="store_true")
    parser.add_argument("--preview", help="preview parsed rally config without running the bot", action="store_true")

    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="run the bot")
    run_parser.add_argument("--dump", help="dump online rally config to yaml after running", action="store_true")

    subparsers.add_parser("preview", help="preview the rally config")
    subparsers.add_parser("dump", help="dump config file to yaml")

    args = parser.parse_args()

    logger = get_logger(verbose=args.verbose)
    try:
        config = Config.from_path(logger=logger, path=args.input, name=args.name, password=args.password)
    except Exception:
        logger.exception("Error while reading config")
        return 1

    match args.command:
        case "run":
            bot = Bot(logger, config)
            bot.run()
            if args.dump:
                config.dump()
        case "preview":
            print(config)  # noqa: T201
        case "dump":
            config.dump()

    return 0


def get_logger(*, verbose: bool = False) -> logging.Logger:
    logger = colorlog.getLogger("rsfor")
    level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(level)

    logger.handlers.clear()

    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s[%(levelname)s] %(message)s",
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
