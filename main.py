import logging

import bot

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("main")

logging.getLogger("asyncio").setLevel(logging.INFO)
logging.getLogger("botocore").setLevel(logging.INFO)
logging.getLogger("discord").setLevel(logging.WARNING)
logging.getLogger("s3transfer").setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.INFO)


def main() -> None:
    test = bot.AoE2Bot(command_prefix="$")
    test.run()


if __name__ == "__main__":
    main()
