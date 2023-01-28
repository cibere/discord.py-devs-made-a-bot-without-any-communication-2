import random
from datetime import datetime
from logging import getLogger

import discord
from discord.ext import commands, tasks

from .base_cog import BaseEconomyCog

log = getLogger('BotChallenge.lottery')


class Lottery(BaseEconomyCog):
    """All lottery related commands/tasks"""

    @tasks.loop(minutes=1)
    async def lottery_check(self):
        """Check if any lotteries have ended and draw a winner"""

        async with self.bot.pool.acquire() as conn:
            lottery = await conn.fetchone(
                'SELECT * FROM lottery WHERE winner IS NULL and end_time <= :current_time',
                {'current_time': round(datetime.now().timestamp())},
            )
            await conn.commit()

        if not lottery:
            return

        print(lottery)
        winner = None
        # Check if there are any entrants
        if not lottery['entries']:
            return
        amount = lottery['bal']
        # Split all the user ids into a list
        entrants = lottery['entries'].split(',')
        # Check if there is only one entrant
        if len(entrants) == 1:
            amount *= random.randint(1, 5)
            winner = entrants[0]
        # Pick a winner
        if winner is None:
            winner = random.choice(entrants)
        # Get winner's wallet
        winner = await self.bot.fetch_user(winner)
        wallet = await self.get_wallet(winner)
        # Give the winner their prize
        async with self.bot.pool.acquire() as conn:
            await wallet.add(amount, connection=conn)
            await conn.execute(
                'UPDATE lottery SET winner = :winner WHERE lot_id = :id', {'winner': winner.id, 'id': lottery['lot_id']}
            )
            await conn.commit()
        # Send a message to the winner
        await winner.send(f'You won the lottery! You won {self.currency_symbol}{lottery["bal"]}')
        log.info(f"Lottery ended. Winner: {winner} (ID: {winner.id})")

    # Create a lottery at random
    @tasks.loop(hours=1)
    async def create_lottery(self):
        chance = random.randint(1, 100)
        # 20% chance of a lottery starting
        if chance > 20:
            return

        log.info("Starting a lottery")

        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                'INSERT INTO lottery (bal, entries, start_time, end_time) VALUES (:start_bal, :entries, :start_time, :end_time)',
                {
                    'start_time': round(datetime.now().timestamp()),
                    'end_time': round(datetime.now().timestamp()) + 3600,
                    'start_bal': 0,
                    'entries': None,
                },
            )
            await conn.commit()

    @lottery_check.before_loop
    async def before_lottery_check(self):
        await self.bot.wait_until_ready()

    # View the currently running lottery
    @commands.command()
    async def lottery(self, ctx: commands.Context):
        """View the currently running lottery"""

        async with self.bot.pool.acquire() as conn:
            lottery = await conn.fetchone(
                'SELECT * FROM lottery WHERE start_time < :current_time AND end_time > :current_time',
                {'current_time': round(datetime.now().timestamp())},
            )
            await conn.commit()

        if not lottery:
            return await ctx.send('There is no lottery running at the moment')
        embed = discord.Embed(title='Lottery', description=f'Lottery ID: {lottery["lot_id"]}')
        embed.add_field(name='Prize', value=f'{self.currency_symbol}{lottery["bal"]}', inline=False)
        # Split all the user ids into a list
        entrants = lottery['entries'].split(',') if lottery['entries'] else ''
        embed.add_field(name='Participants', value=f'{len(entrants)}', inline=False)
        embed.add_field(
            name='Winner', value=f'{lottery["winner"] if lottery["winner"] == 0 else "Not yet drawn"}', inline=False
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=['startlottery'])
    @commands.is_owner()
    async def start_lottery(self, ctx: commands.Context, duration: int):
        """Start a lottery with a duration in minutes"""

        duration = duration * 60

        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                'INSERT INTO lottery (bal, entries, start_time, end_time) VALUES (:start_bal, :entries, :start_time, :end_time)',
                {
                    'start_time': round(datetime.now().timestamp()),
                    'end_time': round(datetime.now().timestamp()) + duration,
                    'start_bal': 0,
                    'entries': None,
                },
            )
            await conn.commit()

        await ctx.send(f'Lottery started for {duration/60} minutes')

    @commands.command(alias=['endlottery'])
    @commands.is_owner()
    async def end_lottery(self, ctx: commands.Context, lottery_id: int):
        """End a lottery"""

        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                'UPDATE lottery SET end_time = :end_time WHERE lot_id = :id', {'end_time': 0, 'id': lottery_id}
            )
            await conn.commit()

        await ctx.send('Lottery ended')

    @commands.command()
    async def enter(self, ctx: commands.Context):
        """Enter the lottery"""

        async with self.bot.pool.acquire() as conn:
            lottery = await conn.fetchone(
                'SELECT * FROM lottery WHERE start_time < :current_time AND end_time > :current_time',
                {'current_time': round(datetime.now().timestamp())},
            )
            await conn.commit()

        if not lottery:
            return await ctx.send('There is no lottery running at the moment')

        wallet = await self.get_wallet(ctx.author)
        if wallet.balance < 25:
            return await ctx.send('You need at least 25 to enter the lottery')

        async with self.bot.pool.acquire() as conn:
            await wallet.withdraw(25, connection=conn)
            # Fetch current entries
            lottery = await conn.fetchone('SELECT * FROM lottery WHERE lot_id = :id', {'id': lottery['lot_id']})
            if not lottery['entries']:
                entries = str(ctx.author.id)
            else:
                entries = f'{lottery["entries"]},{ctx.author.id}'
            await conn.execute(
                'UPDATE lottery SET entries = :entries, bal = :bal, entries = :entries WHERE lot_id = :id',
                {
                    'entries': f'{lottery["entries"]},{ctx.author.id}',
                    'bal': lottery['bal'] + 25,
                    'entries': entries,
                    'id': lottery['lot_id'],
                },
            )
            await conn.commit()

        await ctx.send(f'You entered the lottery for {self.currency_symbol}25')
