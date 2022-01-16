import logging

from discord.ext import commands  # type: ignore


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
