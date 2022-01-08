import asyncio
from collections import defaultdict
import csv
import datetime
import io
import json
import logging
import os
import sys
from typing import Optional, Dict, Any, List, Tuple, Union

import discord  # type: ignore
from discord.ext import commands  # type: ignore

import aoe2net
import utils

# for pcm audio hotfix
import subprocess
import shlex
from discord.opus import Encoder  # type: ignore


class CommandErrorHandler(commands.Cog):
    log: logging.Logger
    _bot: commands.Bot

    def __init__(self, bot: commands.Bot, bot_name: str) -> None:
        """
        Initialize the CommandErrorHandler cog.

        :param bot: The bot the cog is attached to
        :param bot_name: The name of the bot for logging purposes
        """
        self.log = logging.getLogger(f"{bot_name}.{self.__class__.__name__}")
        self._bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error) -> None:
        """

        :param ctx: The bot context
        :param error: The error that occurred
        """
        self.log.error(f"{type(error)} - '{ctx.command} {ctx.args}' '{error}'")

        text: str = "An error occurred, please contact your administrator."
        if isinstance(error, commands.MissingRequiredArgument):
            text = f"Invalid use of {ctx.command}, see !help."
        elif isinstance(error, commands.CommandNotFound):
            text = f"Command does not exist."
        else:
            self.log.exception("Unhandled exception occurred")

        await ctx.send(text)


class FFmpegPCMAudio(discord.AudioSource):
    # https://github.com/Rapptz/discord.py/issues/5192
    def __init__(
        self,
        source,
        *,
        executable="ffmpeg",
        pipe=False,
        stderr=None,
        before_options=None,
        options=None,
    ):
        stdin = None if not pipe else source
        args = [executable]
        if isinstance(before_options, str):
            args.extend(shlex.split(before_options))
        args.append("-i")
        args.append("-" if pipe else source)
        args.extend(("-f", "s16le", "-ar", "48000", "-ac", "2", "-loglevel", "warning"))
        if isinstance(options, str):
            args.extend(shlex.split(options))
        args.append("pipe:1")
        self._process = None
        try:
            self._process = subprocess.Popen(
                args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr
            )
            self._stdout = io.BytesIO(self._process.communicate(input=stdin)[0])
        except FileNotFoundError:
            raise discord.ClientException(executable + " was not found.") from None
        except subprocess.SubprocessError as exc:
            raise discord.ClientException(
                "Popen failed: {0.__class__.__name__}: {0}".format(exc)
            ) from exc

    def read(self):
        ret = self._stdout.read(Encoder.FRAME_SIZE)
        if len(ret) != Encoder.FRAME_SIZE:
            return b""
        return ret

    def cleanup(self):
        proc = self._process
        if proc is None:
            return
        proc.kill()
        if proc.poll() is None:
            proc.communicate()

        self._process = None


class Taunt(commands.Cog):
    log: logging.Logger
    _bot: commands.Bot
    _space: str = "aoe2taunts"
    _manifest_name: str = "manifest.json"
    _do_api: utils.DigitalOcean
    _manifest: List[Dict[str, Any]]

    def __init__(
        self,
        bot: commands.Bot,
        bot_name: str,
        space: Optional[str] = None,
        manifest: str = "manifest.json",
    ) -> None:
        """
        Initialize the Taunt cog.

        :param bot: The bot the cog is attached to
        :param bot_name: The name of the bot for logging purposes
        :param space: The name of the space/bucket to use
        :param manifest: The name of the manifest file to use
        """
        self.log = logging.getLogger(f"{bot_name}.{self.__class__.__name__}")

        if space:
            self._space = space

        self._bot = bot

        self._do_api = utils.DigitalOcean()
        self._manifest = json.load(self._do_api.get_object(self._space, manifest))
        self._taunt_min, self._taunt_max = self.get_taunt_range()

        if "linux" in sys.platform:
            discord.opus.load_opus("libopus.so.0")
            if not discord.opus.is_loaded():
                raise Exception("Opus failed to load")

        self.log.info(f"Registered {self.__class__.__name__} cog to {bot_name}")

    def get_taunt_range(self) -> Tuple[int, int]:
        min_num: int = 1
        max_num: int = 1
        for taunt in self._manifest:
            if taunt["num"] < min_num:
                min_num = taunt["num"] = min_num
            if taunt["num"] > max_num:
                max_num = taunt["num"]
        return min_num, max_num

    def get_taunt_text(self, num: int) -> str:
        for taunt in self._manifest:
            if taunt["num"] == num:
                return taunt["text"]
        raise ValueError

    def get_taunt_audio(self, num: int) -> Any:
        for taunt in self._manifest:
            if taunt["num"] == num:
                return self._do_api.get_object(self._space, taunt["file"])
        return None

    @commands.command()
    async def taunt(self, ctx, number: int) -> None:
        """
        Plays AoE2:DE taunt.

        Usage: !taunt <number>
        """

        taunt_text: Optional[str]
        try:
            taunt_text = self.get_taunt_text(number)
        except ValueError:
            taunt_text = (
                f"Taunts must be between {self._taunt_min} and {self._taunt_max}."
            )

        await ctx.send(taunt_text)

        # check if sender is in a voice channel
        if not ctx.author.voice:
            return

        if ctx.author.voice.channel:
            if ctx.bot.voice_clients:
                voice_client: discord.VoiceClient = ctx.bot.voice_clients[0]
                if voice_client.channel != ctx.author.voice.channel:
                    await voice_client.move_to(ctx.author.voice.channel)
            else:
                voice_client = await ctx.author.voice.channel.connect(timeout=10)  # type: ignore

            taunt_audio: io.BytesIO = self.get_taunt_audio(number)

            voice_client.play(FFmpegPCMAudio(taunt_audio.read(), pipe=True))
            while voice_client.is_playing():
                await asyncio.sleep(5)

            taunt_audio.close()

            # await voice_client.disconnect()


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
            player: Optional[Dict[str, Any]] = self._aoe2_api.find_name(
                name, board=aoe2net.AoE2net.LeaderboardID.ALL
            )
            if player is None:
                raise ValueError(f"Failed to fetch player {player}")

            profile_id: Union[str, int] = player["profile_id"]
            matches: List[Dict[str, Any]] = self._aoe2_api.matches(
                profile_ids=profile_id
            )
            stats: Dict[str, Any] = {"name": name, "stats": defaultdict(defaultciv)}
            for match in matches:
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
            player_stats.append(stats)

        data: io.StringIO = io.StringIO()
        writer: csv.DictWriter = csv.DictWriter(
            data, ["player", "civ", "wins", "losses", "custom", "total"]
        )
        writer.writeheader()
        for player in player_stats:
            for civ, stats in player["stats"].items():
                row: Dict[str, Any] = {"player": player["name"]}
                row.update({"civ": civ})
                row.update(stats)
                writer.writerow(row)
        data.seek(0)

        date: str = datetime.datetime.now().date().strftime("%Y%m%d_")
        await ctx.send(
            file=discord.File(data, filename=date + "_".join(players) + ".csv")
        )


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
        Check a player's elo. Player names with spaces must be in quotes.

        Usage: !elo <player_name> <game_type>
            - player_name:
                The player's username
            - game_type (optional):
                This can be any of the following options:
                    - "all": All leaderboards, default
                    - "solo": 1v1 Random Map Only
                    - "team": Team Random Map Only

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
        self.add_cog(Taunt(self, self.__class__.__name__))
        self.add_cog(Civs(self, self.__class__.__name__))
        self.add_cog(CommandErrorHandler(self, self.__class__.__name__))

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
