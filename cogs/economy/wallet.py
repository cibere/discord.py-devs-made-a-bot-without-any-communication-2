import discord
from discord.ext import commands

from .base_cog import BaseEconomyCog


class WalletManagement(BaseEconomyCog):
    """Commands to manage, send, and receive money."""

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
        await ctx.send('Transfered money.')
