import sqlite3

import discord
from discord.ext import commands

from main import BotChallenge


class Wallet:
    def __init__(self, data: sqlite3.Row, bot: BotChallenge) -> None:
        self._bot = bot
        self.user_id = data['user_id']
        self._balance = data['balance']

    @property
    def balance(self):
        return self._balance


class BaseEconomyCog(commands.Cog):
    """Class with methods that are useful / needed for other functionality."""

    currency_symbol = '€'
    currency_name = 'E-Coins'

    def __init__(self, bot: BotChallenge) -> None:
        self.bot: BotChallenge = bot
        super().__init__()

    async def cog_check(self, ctx: commands.Context) -> bool:
        if not ctx.command:
            return True
        check = (
            await self.bot.db.fetchone(
                'SELECT EXISTS(SELECT user_id FROM wallets WHERE user_id = ?) AS value', (ctx.author.id,)
            )
        )['value']
        if not check:
            if ctx.command.name != 'start':
                raise commands.CheckFailure('You do not have a wallet, use the command "start" to get one')
            return True
        if ctx.command.name == 'start':
            raise commands.CheckFailure('You already have a wallet')
        return True

    async def get_wallet(self, user: discord.abc.User) -> Wallet:
        wallet_info = await self.bot.db.fetchone('SELECT * FROM wallets WHERE user_id = ?', (user.id,))
        return Wallet(wallet_info, self.bot)
