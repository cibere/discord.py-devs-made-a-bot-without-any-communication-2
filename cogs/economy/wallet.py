import discord
from discord.ext import commands

from .base_cog import BaseEconomyCog


class WalletManagement(BaseEconomyCog):
    """Commands to manage, send, and receive money."""

    @commands.command()
    async def start(self, ctx: commands.Context):
        """Opens a wallet for you"""
        await self.bot.db.execute('INSERT INTO wallets (user_id) VALUES (?) ON CONFLICT DO NOTHING', (ctx.author.id,))
        await ctx.send('You have succesfully started :) welcome to the economy')

    @commands.command(aliases=['bal'])
    async def balance(self, ctx: commands.Context, user: discord.Member | discord.User = commands.Author):
        """Checks yours or someone else's balance"""
        wallet = await self.get_wallet(user)
        await ctx.send(f'{user} has {self.currency_symbol}{wallet.balance}')
