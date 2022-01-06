import argparse
import logging

import bot

logging.basicConfig(level=logging.DEBUG)
log: logging.Logger = logging.getLogger("main")

logging.getLogger("asyncio").setLevel(logging.INFO)
logging.getLogger("botocore").setLevel(logging.INFO)
logging.getLogger("discord").setLevel(logging.INFO)
logging.getLogger("s3transfer").setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.INFO)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Default")
    parser.add_argument("--debug", help="debug", action="store_true")
    return parser.parse_args()


def main() -> None:
    args: argparse.Namespace = parse_args()

    prefix: str = "$" if args.debug else "!"
    test = bot.AoE2Bot(args.debug, command_prefix=prefix)
    test.run()


if __name__ == "__main__":
    main()
