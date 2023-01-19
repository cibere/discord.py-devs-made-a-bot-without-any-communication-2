import sys
import sqlite3
from contextlib import asynccontextmanager
from typing import Optional, Dict

import asqlite
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

    async def update_values(self):
        async with self.managed_conn() as conn:
            wallet_info = await conn.fetchone('SELECT * FROM wallets WHERE user_id = ?', (self.user_id,))
        self.__init__(wallet_info, self._bot)

    @asynccontextmanager
    async def managed_conn(self, connection: Optional[asqlite.Connection] = None):
        """Async context manager that creates a connection
        and manages it if no connection is passed to it.
        """
        context_manager = None
        try:
            if connection is None:
                context_manager = self._bot.pool.acquire()
                connection = await context_manager
            yield connection
        finally:
            if context_manager:
                await connection.commit()
                await context_manager.__aexit__(*sys.exc_info())

    async def withdraw(self, amount: int, /, *, connection: Optional[asqlite.Connection] = None):
        """|coro|

        Withdraws money from this wallet.

        Parameter
        ---------
        amount: int
            The amount of money to withdraw.
        connection: Optional[asqlite.Connection]
            An optional connection to use, if not passed, this
            method will acquire and manage it's own connection.
        """
        if amount > self.balance:
            raise commands.BadArgument(f'You do not have enough money. You have {self.balance}')
        self._balance -= amount
        async with self.managed_conn(connection) as conn:
            data = await conn.fetchone(
                'UPDATE wallets SET balance = balance - ? WHERE user_id = ? RETURNING balance', (amount, self.user_id)
            )
            self._balance = data['balance']

    async def add(self, amount: int, /, *, connection: Optional[asqlite.Connection] = None):
        """|coro|

        Adds money to this wallet.

        Parameter
        ---------
        amount: int
            The amount of money to add.
        connection: Optional[asqlite.Connection]
            An optional connection to use, if not passed, this
            method will acquire and manage it's own connection.
        """
        async with self.managed_conn(connection) as conn:
            data = await conn.fetchone(
                'UPDATE wallets SET balance = balance + ? WHERE user_id = ? RETURNING balance', (amount, self.user_id)
            )
            self._balance = data['balance']


class BaseEconomyCog(commands.Cog):
    """Class with methods that are useful / needed for other functionality."""

    currency_symbol = '€'
    currency_name = 'E-Coins'

    def __init__(self, bot: BotChallenge) -> None:
        self.bot: BotChallenge = bot
        super().__init__()
        self._wallets: Dict[int, Wallet] = {}

    async def cog_check(self, ctx: commands.Context) -> bool:
        """Check so that all commands have you entered in the database, but with a special case for start."""
        if not ctx.command:
            return True
        async with self.bot.pool.acquire() as conn:
            check = (
                await conn.fetchone(
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
        """|coro|

        Gets a wallet from cache, or creates one from database if it doesn't exist

        Parameter
        ---------
        user: discord.abc.User
            The owner of the wallet you are trying to get.

        Raises
        ------
        commands.BadArgument
            The user has not started in economy.

            Why bad argument? It hooks into the error handler.
        """
        wallet = self._wallets.get(user.id)
        if wallet:
            return wallet
        async with self.bot.pool.acquire() as conn:
            wallet_info = await conn.fetchone('SELECT * FROM wallets WHERE user_id = ?', (user.id,))
        if wallet_info:
            wallet = Wallet(wallet_info, self.bot)
            self._wallets[user.id] = wallet
            return wallet
        raise commands.BadArgument(f'Wallet not found.')
