from .item_store import ItemStore
from .lottery import Lottery
from .wallet import WalletManagement
from .trivia import Trivia


class Economy(WalletManagement, ItemStore, Lottery, Trivia):
    """Economy commands, the 'start' command to get started."""

    async def cog_load(self):
        self.lottery_check.start()
        await self.get_items()


async def setup(bot):
    await bot.add_cog(Economy(bot))
