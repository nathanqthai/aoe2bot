import logging
import os
from typing import Optional

import discord  # type: ignore
from discord.ext import commands  # type: ignore

from aoe2bot.cogs import civs, elo, error, taunt


class AoE2Bot(commands.Bot):
    """An AoE2 Discord Bot"""

    log: logging.Logger
    __token: Optional[str] = None

    async def on_ready(self) -> None:
        """
        Called when the bot is read.

        :return: None
        """
        self.log.debug(f"Logged in as {self.user}")

    def add_cogs(self) -> None:
        """Adds all cogs"""
        self.add_cog(elo.ELO(self, self.__class__.__name__))
        self.add_cog(taunt.Taunt(self, self.__class__.__name__))
        self.add_cog(civs.Civs(self, self.__class__.__name__))
        self.add_cog(error.CommandErrorHandler(self, self.__class__.__name__))

    def run(self) -> None:
        super().run(self.__token)

    def __init__(self, debug: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)

        self.log = logging.getLogger(f"{self.__class__.__name__}")

        token_env = "DISCORD_BOT_TOKEN"
        if debug:
            token_env += "_DEV"
        self.__token = os.getenv(token_env)
        if self.__token is None:
            self.log.error(f"Invalid token in {token_env} env var!")

        self.add_cogs()
