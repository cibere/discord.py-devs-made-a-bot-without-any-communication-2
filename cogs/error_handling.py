from logging import getLogger

import discord
from discord.ext import commands

log = getLogger(__name__)


@commands.Cog.listener()
async def on_command_error(ctx: commands.Context, error: Exception):
    """|coro|

    Handles errors for the bot. Errors that are not handled here get logged to the console
    """
    if isinstance(error, commands.CommandInvokeError):
        error = error.original

    ignored = (commands.CommandNotFound, commands.NotOwner, commands.MissingPermissions)

    if isinstance(error, ignored):
        return log.debug(f'Ignoring error for {ctx.author}: {error}', exc_info=False)

    if isinstance(error, (commands.UserInputError, commands.CheckFailure)):
        return await ctx.send(str(error))

    await ctx.send('Something went wrong...')

    metadata = [
        f"ERROR METADATA:",
        f'user: {ctx.author}',
    ]
    if isinstance(ctx.author, discord.Member):
        metadata.extend(
            [
                f'guild: {ctx.guild}',
                f'author permissions: {ctx.author.guild_permissions}',
                f'bot permissions: {getattr(ctx.me, "guild_permissions")}',
            ]
        )

    log.error('\n'.join(metadata), exc_info=error)


async def setup(bot: commands.Bot):
    bot.add_listener(on_command_error)
