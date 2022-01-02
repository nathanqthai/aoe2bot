import io
import json
import logging
import os
import time
from typing import Optional, Dict, Any, List, Tuple

import discord  # type: ignore
from discord.ext import commands  # type: ignore

import aoe2net
import utils


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

    async def on_voice_state_update(self, member, before, after):
        voice_state = member.guild.voice_client
        # Checking if the bot is connected to a channel and if there is only 1 member connected to it (the bot itself)
        if voice_state is not None and len(voice_state.channel.members) == 1:
            # You should also check if the song is still playing
            await voice_state.disconnect()

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
        author_voice: discord.member.VoiceState = ctx.author.voice
        if not author_voice:
            return

        author_channel: discord.VoiceChannel = author_voice.channel
        if author_channel:
            for client_channel in ctx.bot.voice_clients:
                if author_channel != client_channel:
                    await client_channel.disconnect()
                    break

            voice_client: discord.VoiceClient = await author_channel.connect(timeout=10)  # type: ignore

            taunt_audio: io.BytesIO = self.get_taunt_audio(number)

            voice_client.play(discord.PCMAudio(taunt_audio))
            while voice_client.is_playing():
                time.sleep(0.1)

            taunt_audio.close()

            await voice_client.disconnect()


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
        self.add_cog(CommandErrorHandler(self, self.__class__.__name__))

    def run(self) -> None:
        super().run(self.__token)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.log = logging.getLogger(f"{self.__class__.__name__}")

        self.__token = os.getenv("DISCORD_BOT_TOKEN")
        if self.__token is None:
            self.log.error("Invalid token in DISCORD_BOT_TOKEN env var!")

        self.add_cogs()
