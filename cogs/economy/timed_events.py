import random
from discord.ext import tasks

from .base_cog import BaseEconomyCog


class TimedEvents(BaseEconomyCog):
    """Cog for all the timed events in the bot"""

    async def cog_load(self):
        self.robbery.start()

    @tasks.loop(minutes=25)
    async def robbery(self):
        """Robbery event"""

        chance = random.randint(1, 100)
        if chance < 85:
            return

        # Select random user from the database
        async with self.bot.pool.acquire() as conn:
            user = await conn.fetchone(
                'SELECT * FROM users WHERE bal > :bal_limit ORDER BY RANDOM() LIMIT 1', {'bal_limit': 25}
            )
            await conn.commit()

        if not user:
            return

        # Get the user's wallet
        wallet = await self.get_wallet(user['user_id'])

        # Pick the amount to steal
        amount = random.randint(1, wallet.balance - 1)

        # Steal
        async with self.bot.pool.acquire() as conn:
            await wallet.withdraw(amount, connection=conn)
            await conn.commit()

        # Send message
        channel = await self.bot.fetch_user(wallet.user_id)
        await channel.send(f'You were robbed! You lost {self.currency_symbol}{amount}')

    @robbery.before_loop
    async def before_robbery(self):
        await self.bot.wait_until_ready()
