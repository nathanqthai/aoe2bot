import asyncio
import io
import json
import logging
import shlex
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple

import discord  # type: ignore
from discord.ext import commands  # type: ignore
from discord.opus import Encoder  # type: ignore

from aoe2bot.cogs.api.digitalocean import DigitalOcean


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
    _do_api: DigitalOcean
    _manifest: List[Dict[str, Any]]
    loop: bool = False

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

        self._do_api = DigitalOcean()
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
    async def stop(self, ctx) -> None:
        self.loop = False

    @commands.command(aliases=["t"])
    async def taunt(self, ctx, number: int, delay: Optional[int] = None) -> None:
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

            taunt_audio: io.BytesIO
            while True:
                taunt_audio = self.get_taunt_audio(number)
                voice_client.play(
                    FFmpegPCMAudio(taunt_audio.read(), pipe=True)
                )
                while voice_client.is_playing():
                    await asyncio.sleep(1)

                if delay:
                    await asyncio.sleep(float(delay))

                if not self.loop:
                    break

            taunt_audio.close()
