from typing import Optional

import discord
import tabulate
from discord.ext import commands

from .base_cog import BaseEconomyCog, Item


class ItemStore(BaseEconomyCog):
    @commands.command()
    async def buy(self, ctx: commands.Context, amount: Optional[int], *, item_name: str):
        """Buys one or more items from the store."""
        amount = amount or 1

        def pred(item: Item) -> bool:
            return item.name.lower() == item_name.lower()

        item = discord.utils.find(pred, self.items.values())
        if not item:
            raise commands.BadArgument('There is no item with that name.')
        price = item.price * amount
        wallet = await self.get_wallet(ctx.author)
        await wallet.withdraw(price)
        wallet.inventory[item.item_id] += 1
        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                'INSERT INTO inventory (user_id, item_id, amount) VALUES (:user_id, :item_id, :amount)'
                '\nON CONFLICT DO UPDATE SET amount = amount + :amount',
                {'user_id': ctx.author.id, 'item_id': item.item_id, 'amount': amount},
            )
            await conn.commit()
        await ctx.send(f'You bough {amount} {item.name} for a total of {self.currency_symbol}{price}')

    @commands.command()
    async def sell(self, ctx: commands.Context, amount: Optional[int], *, item_name: str):
        """Sells one or more items back to the store"""
        amount = amount or 1

        def pred(item: Item) -> bool:
            return item.name.lower() == item_name.lower()

        item = discord.utils.find(pred, self.items.values())
        if not item:
            raise commands.BadArgument('There is no item with that name.')
        wallet = await self.get_wallet(ctx.author)
        if wallet.inventory[item.item_id] - amount < 1:
            raise commands.BadArgument(f'You do not have that many of {item.name}')
        wallet.inventory[item.item_id] -= amount
        price = item.price * amount
        await wallet.add(price)

        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                'UPDATE inventory SET amount = amount - :amount WHERE user_id = :user_id AND item_id = :item_id',
                {'user_id': ctx.author.id, 'item_id': item.item_id, 'amount': amount},
            )
            await conn.commit()

        await ctx.send(f'You sold {amount} {item.name} and earned {self.currency_symbol}{price}')

    @commands.command()
    async def store(self, ctx: commands.Context):
        """Shows the items available to be bought."""
        items = [(item.name, item.price) for item in sorted(self.items.values(), key=lambda i: i.price, reverse=True)]
        table = tabulate.tabulate(items, headers=('Item Name', 'Price'), tablefmt='grid')
        embed = discord.Embed(title='Item Store', color=discord.Color.blurple(), description=f'```py\n{table}\n```')
        embed.set_footer(text='Buy items with `buy`.')
        await ctx.send(embed=embed)