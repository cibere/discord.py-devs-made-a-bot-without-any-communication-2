import os
import asyncio
from logging import getLogger

import discord
from dotenv import load_dotenv
from discord.ext import commands

import asqlite

load_dotenv()
log = getLogger('BotChallenge.main')

INITIAL_EXTENSIONS = ['jishaku', 'cogs.economy', 'cogs.error_handling']


def getenv(key: str) -> str:
    value = os.getenv(key)
    if value:
        return value
    raise RuntimeError(f'{key} not set in .env file')


class BotChallenge(commands.Bot):
    def __init__(self, db: asqlite.Pool) -> None:
        super().__init__(
            command_prefix=commands.when_mentioned_or(getenv('PREFIX')),
            intents=discord.Intents.all(),
            description='6 devs made this bot together, what will happen? Dun dun dun...',
        )
        self.pool = db

    async def setup_hook(self) -> None:
        for ext in INITIAL_EXTENSIONS:
            await self.load_extension(ext)

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user} (ID: {self.user.id})")


async def runner():
    populated = os.path.exists('database.db')

    async with asqlite.create_pool('database.db') as pool, BotChallenge(pool) as bot:
        discord.utils.setup_logging()

        # Creating a database so you don't need to!
        if not populated:
            with open('schema.sql') as f:
                data = f.readlines()
            async with pool.acquire() as conn:
                ret = []
                for line in data:
                    ret.append(line)
                    if ';' in line:
                        query = ''.join(ret)
                        if query.strip():
                            await conn.execute(query)
                        ret = []
                if ret:
                    query = ''.join(ret)
                    if query.strip():
                        await conn.execute(query)
                await conn.commit()
            log.warning('Automatically created a database file! Operation succseful.')
        await bot.start(getenv('TOKEN'))


if __name__ == '__main__':
    asyncio.run(runner())
