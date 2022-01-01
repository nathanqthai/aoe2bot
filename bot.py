import os
import logging
from typing import Optional, Dict, Any, List

from discord.ext import commands  # type: ignore

import aoe2net


class ELO(commands.Cog):
    """Fetches a players ELO rating."""

    log: logging.Logger
    _bot: commands.Bot
    _aoe2_api: aoe2net.AoE2net

    def __init__(self, bot: commands.Bot, bot_name: str) -> None:
        """
        Initialize the ELO cog.

        :param bot: The bot the cog is attached to
        :param bot_name: The name of the bot for logging purposes
        """
        self.log = logging.getLogger(f"{bot_name}.{self.__class__.__name__}")

        self._bot = bot
        self._aoe2_api = aoe2net.AoE2net()

        self.log.info(f"Registered {self.__class__.__name__} cog to {bot_name}")

    @staticmethod
    def get_boards(game_type: str) -> List[aoe2net.AoE2net.LeaderboardID]:
        """
        Parse the game_type subcommand to determine which leaderboards to check.

        :param game_type: A command specifying the game type, defaults to all
        :return: A list of leaderboards to check
        """
        boards: List[aoe2net.AoE2net.LeaderboardID]
        if game_type.lower() in ["unranked"]:
            boards = [aoe2net.AoE2net.LeaderboardID.UNRANKED]
        elif game_type.lower() in ["solo"]:
            boards = [aoe2net.AoE2net.LeaderboardID.RANDOM_MAP]
        elif game_type.lower() in ["team"]:
            boards = [aoe2net.AoE2net.LeaderboardID.TEAM_RANDOM_MAP]
        else:
            boards = [
                aoe2net.AoE2net.LeaderboardID.UNRANKED,
                aoe2net.AoE2net.LeaderboardID.DEATHMATCH,
                aoe2net.AoE2net.LeaderboardID.TEAM_DEATHMATCH,
                aoe2net.AoE2net.LeaderboardID.RANDOM_MAP,
                aoe2net.AoE2net.LeaderboardID.TEAM_RANDOM_MAP,
                aoe2net.AoE2net.LeaderboardID.EMPIRE_WARS,
                aoe2net.AoE2net.LeaderboardID.TEAM_EMPIRE_WARS,
            ]
        return boards

    @commands.command()
    async def elo(self, ctx, name, game_type: str = "all") -> None:
        """
        Implements the !elo command.

        :param ctx: The discord context
        :param name: The player name to lookup
        :param game_type: The game type command that specifies the leaderboard
        :return: None
        """
        self.log.info(f"Looking up player {name}")

        boards: List[aoe2net.AoE2net.LeaderboardID] = self.get_boards(game_type)

        results: List[str] = [f"Ratings for `{name}`:"]
        for board in boards:
            board_str = self._aoe2_api.lookup_string("leaderboard", board.value)

            try:
                player: Optional[Dict[str, Any]] = self._aoe2_api.find_name(
                    name, board=board
                )
                if player:
                    rating: str = player["rating"]
                    result: str = f"- {board_str}: *{rating}*"
                    results.append(result)
            except Exception:
                self.log.exception(f"Error looking up {name}")
                await ctx.send(
                    "Encountered an error, please contact your administrator."
                )
                return

        if len(results) == 1:
            results = [f"Could not find any results for `{name}`!"]
        await ctx.send("\n".join(results))


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
        self.add_cog(ELO(self, self.__class__.__name__))

    def run(self) -> None:
        super().run(self.__token)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.log = logging.getLogger(f"{self.__class__.__name__}")

        self.__token = os.getenv("DISCORD_BOT_TOKEN")
        if self.__token is None:
            self.log.error("Invalid token in DISCORD_BOT_TOKEN env var!")

        self.add_cogs()
