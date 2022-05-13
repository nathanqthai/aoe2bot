from collections import defaultdict
import csv
import datetime
import logging
import io
from typing import Any, Dict, List, Union

import discord  # type: ignore
from discord.ext import commands  # type: ignore

from aoe2bot.cogs.api import aoe2net


class Civs(commands.Cog):
    """Fetches match history for a list of players"""

    def __init__(self, bot: commands.Bot, bot_name: str) -> None:
        """
        Initialize the Civs cog.

        :param bot: The bot the cog is attached to
        :param bot_name: The name of the bot for logging purposes
        """
        self.log = logging.getLogger(f"{bot_name}.{self.__class__.__name__}")

        self._bot = bot
        self._aoe2_api = aoe2net.AoE2net()

        self.log.info(f"Registered {self.__class__.__name__} cog to {bot_name}")

    @commands.command()
    async def civs(self, ctx, names: str) -> None:
        """
        Summarizes a player's civ history and returns it as a CSV.

        Usage: !matches <players>
            - A comma separated list of player names, must have quotes if there is whitespace

        Examples:
            Get civ stats for  `GL.TheViper`:
                !civ GL.TheViper

            Get civ stats for  `GL.TheViper` and `[aM] Liereyy`:
                !elo "GL.TheViper, [aM] Liereyy"
        """
        players: List[str] = [p.strip() for p in names.split(",")]

        def defaultciv() -> Any:
            return {"wins": 0, "losses": 0, "total": 0, "custom": 0}

        player_stats: List[Dict[str, Any]] = []
        for name in players:
            player: List[Dict[str, Any]] = self._aoe2_api.find_name(name)
            if not player:
                await ctx.send(f"Could not find any results for '{name}'.")
                continue
            profile_id: Union[str, int] = player[0]["profile_id"]

            matches: List[Dict[str, Any]] = self._aoe2_api.matches(
                profile_ids=profile_id
            )
            stats: Dict[str, Any] = {"name": name, "stats": defaultdict(defaultciv)}
            for match in matches:
                # don't count unranked games
                if match["game_type"] == self._aoe2_api.LeaderboardID:
                    continue

                for match_player in match["players"]:
                    if match_player["profile_id"] == profile_id:
                        civ = self._aoe2_api.lookup_string("civ", match_player["civ"])
                        if not civ:
                            break
                        stats["stats"][civ]["total"] += 1
                        win = match_player["won"]
                        if win is None:
                            stats["stats"][civ]["custom"] += 1
                        elif win:
                            stats["stats"][civ]["wins"] += 1
                        else:
                            stats["stats"][civ]["losses"] += 1

                        stats["type"] = match["game_type"]

                        stats["teams"] = {
                            "num_teams": match["teams"]
                        }
            player_stats.append(stats)

        if not player_stats:
            await ctx.send(f"No stats found.")
            return

        data: io.StringIO = io.StringIO()
        writer: csv.DictWriter = csv.DictWriter(
            data, ["player", "civ", "wins", "losses", "custom", "total", "mode"]
        )
        writer.writeheader()
        for ps in player_stats:
            for c, s in ps["stats"].items():
                row: Dict[str, Any] = {"player": ps["name"]}
                row.update({"civ": c})
                row.update(s)
                writer.writerow(row)
        data.seek(0)

        date: str = datetime.datetime.now().date().strftime("%Y%m%d_")
        await ctx.send(
            file=discord.File(data, filename=date + "_".join(players) + ".csv")
        )
