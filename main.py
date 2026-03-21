import argparse
import logging
import sys
from pathlib import Path

import colorlog
import yaml

from bot import Bot
from config import Config

RSFOR_DIR = Path.home() / ".rsfor"
CREDS_FILE = RSFOR_DIR / "creds.yaml"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", help="incrase output verbosity", action="store_true")
    parser.add_argument("--input", "-i", help="rally configuration file or online rally url", type=str)
    parser.add_argument("--name", "-n", help="online rally name", type=str, default="")
    parser.add_argument("--withpassword", "-wp", help="force making online rally with password", type=str, default="")
    parser.add_argument("--dump", help="dump online rally into a yaml file", action="store_true")
    parser.add_argument("--preview", help="preview parsed rally config without running the bot", action="store_true")

    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="run the bot")
    run_parser.add_argument("--dump", help="dump online rally config to yaml after running", action="store_true")

    subparsers.add_parser("preview", help="preview the rally config")
    subparsers.add_parser("dump", help="dump config file to yaml")

    creds_parser = subparsers.add_parser("creds", help="add rsf account credentials")
    creds_parser.add_argument("--username", type=str)
    creds_parser.add_argument("--password", type=str)

    args = parser.parse_args()

    logger = get_logger(verbose=args.verbose)

    match args.command:
        case "run" | "preview" | "dump":
            try:
                config = Config.from_path(logger=logger, path=args.input, name=args.name, password=args.withpassword)
            except Exception:
                logger.exception("Error while reading config")
                return 1

            match args.command:
                case "run":
                    creds = load_creds()
                    bot = Bot(logger, config)
                    bot.run(creds)
                    if args.dump:
                        config.dump()
                case "preview":
                    print(config)  # noqa: T201
                case "dump":
                    config.dump()

        case "creds":
            save_creds(args.username, args.password)

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


def load_creds() -> tuple[str, str]:
    RSFOR_DIR.mkdir(exist_ok=True)

    if not CREDS_FILE.exists():
        CREDS_FILE.write_text("username: \npassword: \n")
        msg = (
            f"Credentials file created at {CREDS_FILE}. "
            "Use 'rsfor creds --username <u> --password <p>' to set your credentials."
        )
        raise FileNotFoundError(msg)

    data = yaml.safe_load(CREDS_FILE.read_text())
    username = data.get("username", "")
    password = data.get("password", "")

    if not username or not password:
        msg = (
            "Credentials is not provided. "
            "Please use Use 'rsfor creds --username <u> --password <p>' to set your credentials."
        )
        raise ValueError(msg)

    return username, password


def save_creds(username: str, password: str) -> None:
    RSFOR_DIR.mkdir(exist_ok=True)
    CREDS_FILE.write_text(f"username: {username}\npassword: {password}\n")


if __name__ == "__main__":
    sys.exit(main())
