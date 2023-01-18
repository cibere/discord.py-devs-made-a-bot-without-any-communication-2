import os
import asyncio

import discord
from dotenv import load_dotenv
from discord.ext import commands

import asqlite

load_dotenv()

INITIAL_EXTENSIONS = ['jishaku', 'cogs.economy', 'cogs.error_handling']


def getenv(key: str) -> str:
    value = os.getenv(key)
    if value:
        return value
    raise RuntimeError(f'{key} not set in .env file')


class BotChallenge(commands.Bot):
    def __init__(self, db: asqlite.Connection) -> None:
        super().__init__(
            command_prefix=commands.when_mentioned_or(getenv('PREFIX')),
            intents=discord.Intents.all(),
            description='6 devs made this bot together, what will happen? Dun dun dun...\n\nCommands:',
        )
        self.db = db

    async def setup_hook(self) -> None:
        for ext in INITIAL_EXTENSIONS:
            await self.load_extension(ext)


async def runner():
    async with asqlite.connect('database.db') as conn, BotChallenge(conn) as bot:
        discord.utils.setup_logging()
        await bot.start(getenv('TOKEN'))


if __name__ == '__main__':
    asyncio.run(runner())
