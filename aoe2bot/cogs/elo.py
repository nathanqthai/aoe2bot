import logging
from typing import Any, Dict, List

from discord.ext import commands  # type: ignore

from aoe2bot.cogs.api import aoe2net


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

    @commands.command()
    async def elo(self, ctx, name) -> None:
        """
        Check a player's elo. Player names with spaces must be in quotes.

        Usage: !elo <player_name> <game_type>
            - player_name:
                The player's username

        Examples:
            Get all ELOs for player `GL.TheViper`:
                !elo GL.TheViper

            Get 1v1 Random Map ELO for `GL.TheViper`:
                !elo GL.TheViper solo

            Get Team Random Map ELO for `GL.TheViper`:
                !elo GL.TheViper team

            Get ELO for a player with a space in the name:
                !elo "[aM] Liereyy"
        """
        self.log.info(f"Looking up player {name}")

        results: List[str] = [f"Ratings for `{name}`:"]
        boards: List[Dict[str, Any]] = self._aoe2_api.find_name(name)
        for board in boards:
            try:
                board_str = self._aoe2_api.lookup_string(
                    "leaderboard", board["leaderboard"].value
                )
                rating: str = board["rating"]
                result: str = f"- {board_str}: *{rating}*"
                results.append(result)
            except Exception as e:
                self.log.exception(f"Error looking up {name}")
                raise e

        if len(results) == 1:
            results = [f"Could not find any results for `{name}`!"]

        await ctx.send("\n".join(results))
