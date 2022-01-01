import os
import logging
from typing import Optional, Dict, Any

import discord
from discord.ext import commands

import aoe2net


class AoE2Bot(commands.Bot):
    __token: Optional[str] = None

    async def on_ready(self):
        self.log.debug(f"Logged in as {self.user}")

    def add_commands(self):
        @self.command(name="elo")
        async def elo(ctx, search_name: str):
            self.log.info(f"Looking up player `{search_name}")
            board: aoe2net.AoE2net.LeaderboardID = aoe2net.AoE2net.LeaderboardID.RANDOM_MAP
            player: Optional[Dict[str, Any]] = None
            try:
                player = self._aoe2_api.find_name(search_name, board=board)

                result: str = f"Player '{search_name}' could not be found!"
                if player:
                    elo = player.get("rating")
                    name = player.get("name")
                    board_str = self._aoe2_api.lookup_string("leaderboard", board.value)
                    board_str = f" in the {board_str} leaderboard" if board_str else ""
                    result = f"{name} is rated {elo}{board_str}."

            except Exception:
                self.log.exception(f"Error looking up {search_name}")
                await ctx.send(
                    "Encountered an error, please contact your administrator."
                )
                return

            await ctx.send(result)

    def run(self) -> None:
        super().run(self.__token)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.log: logging.Logger = logging.getLogger(f"{self.__class__.__name__}")
        self.__token = os.getenv("DISCORD_BOT_TOKEN")
        if self.__token is None:
            self.log.error("Invalid token in DISCORD_BOT_TOKEN env var!")

        self._aoe2_api = aoe2net.AoE2net()
        self.add_commands()
