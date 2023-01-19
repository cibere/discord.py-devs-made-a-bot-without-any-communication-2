import random
import discord
from discord.ext import commands

from .base_cog import BaseEconomyCog


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
            await ctx.send('You have succesfully started :) welcome to the economy')

    @commands.command(aliases=['bal'])
    async def balance(self, ctx: commands.Context, user: discord.User = commands.Author):
        """Checks yours or someone else's balance"""
        wallet = await self.get_wallet(user)
        await ctx.send(f'{user} has {self.currency_symbol}{wallet.balance}')

    @commands.command()
    async def pay(self, ctx: commands.Context, user: discord.User, amount: int):
        """Transfers money to a user."""
        other_wallet = await self.get_wallet(user)
        your_wallet = await self.get_wallet(ctx.author)
        await your_wallet.withdraw(amount)
        await other_wallet.add(amount)
        await ctx.send(f"You gave them {amount} {self.currency_name}")

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
