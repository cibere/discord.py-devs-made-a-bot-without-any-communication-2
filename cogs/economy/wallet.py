import asyncio
import random
from sqlite3 import Row

import discord
from discord.ext import commands

from components import embeds

from .base_cog import BaseEconomyCog


class LeaderboardFlags(commands.FlagConverter, prefix='--', delimiter=' '):
    guild: bool = commands.flag(
        name='guild', default=False, description='Only shows the top people from the current guild', converter=bool
    )


class WalletManagement(BaseEconomyCog):
    """Commands to manage, send, and earn money. Games and other more complex things excluded."""

    WORK_MESSAGES = [  # I need to add more... oh well don't have time!
        'You did freelance work, and earned {}',
        'You delivered a pizza, and got tipped {}',
        'You worked and earned {}',
    ]

    @commands.command()
    async def start(self, ctx: commands.Context):
        """Opens a wallet for you"""
        async with self.bot.pool.acquire() as conn:
            await conn.execute('INSERT INTO wallets (user_id) VALUES (?) ON CONFLICT DO NOTHING', (ctx.author.id,))
            await conn.commit()
            await ctx.send(embed=embeds.Embed.Success('Success', 'You have succesfully started :) welcome to the economy'))

    @commands.command()
    async def quit(self, ctx: commands.Context):
        """Closes your wallet"""
        # Ask the user to confirm
        await ctx.send('Are you sure you want to quit? This will delete all your data. (y/n)')
        try:
            msg = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=10)
        except asyncio.TimeoutError:
            return await ctx.send('You took too long to respond, quitting cancelled.')

        if msg.content.lower() != 'y':
            return await ctx.send('Quitting cancelled.')

        async with self.bot.pool.acquire() as conn:
            await conn.execute('DELETE FROM wallets WHERE user_id = ?', (ctx.author.id,))
            await conn.commit()
            await ctx.send(embed=embeds.Embed.Success('Success', 'You have succesfully quit the economy :('))

    @commands.command(aliases=['bal'])
    async def balance(self, ctx: commands.Context, user: discord.User = commands.Author):
        """Checks yours or someone else's balance"""
        wallet = await self.get_wallet(user)
        await ctx.send(f'`{user}` has `{self.currency_symbol}{wallet.balance}`')

    @commands.command()
    async def pay(self, ctx: commands.Context, user: discord.User, amount: int):
        """Transfers money to a user."""
        other_wallet = await self.get_wallet(user)
        your_wallet = await self.get_wallet(ctx.author)
        await your_wallet.withdraw(amount)
        await other_wallet.add(amount)
        await ctx.send(f"You gave them `{amount} {self.currency_name}`")

    @commands.command()
    @commands.cooldown(1, 5 * 60, commands.BucketType.user)
    async def work(self, ctx: commands.Context):
        """The simplest way to earn money.

        This command can be ran once every 5 minutes."""
        money = random.randint(10, 100)
        wallet = await self.get_wallet(ctx.author)
        await wallet.add(money)
        await ctx.send(random.choice(self.WORK_MESSAGES).format(self.currency_symbol + str(money)))

    @commands.command()
    @commands.cooldown(1, 24 * 60 * 60, commands.BucketType.user)
    async def daily(self, ctx: commands.Context):
        """The simplest way to earn money.

        This command can be ran once every day."""
        money = random.randint(1000, 5000)
        wallet = await self.get_wallet(ctx.author)
        await wallet.add(money)
        await ctx.send(f"Today, you earned {self.currency_symbol}{money}")

    @commands.command(aliases=['lb'])
    async def leaderboard(self, ctx: commands.Context, *, scope: LeaderboardFlags):
        """Displays the leaderboard. The more money you have, the higher you are on the list.

        You can pass a scope flag for a more specific leaderboard.
        `guild` : only shows users from the current guild. Example: `--guild`
        """

        assert ctx.guild is not None
        user_ids_current_guild = [user.id for user in ctx.guild.members]

        if scope.guild is False:
            async with self.bot.pool.acquire() as conn:
                raw_users = await conn.fetchall('SELECT * FROM wallets')
                await conn.commit()
        else:
            async with self.bot.pool.acquire() as conn:
                raw_users = await conn.fetchall('SELECT * FROM wallets WHERE user_id in $1', (user_ids_current_guild))
                await conn.commit()

        def key(row: Row) -> int:
            return row['balance']

        raw_users.sort(key=key, reverse=True)

        table: list[str] = []

        for index, row in enumerate(raw_users):
            user = self.bot.get_user(row['user_id'])
            if not user:
                user = await self.bot.fetch_user(row['user_id'])

            table.append(f"{index + 1}) {self.currency_symbol}{row['balance']} - {f'{user} (ID: {user.id})'}")

        em = discord.Embed(description='\n'.join(table), title='Leaderboard')
        em.set_footer(text=f"Scope: {'guild' if scope.guild else 'global'}")
        await ctx.send(embed=em)
