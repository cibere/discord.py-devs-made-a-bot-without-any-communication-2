from .wallet import WalletManagement
from .item_store import ItemStore
from .lottery import Lottery


class Economy(WalletManagement, ItemStore, Lottery):
    """Economy commands, the 'start' command to get started."""


async def setup(bot):
    await bot.add_cog(Economy(bot))
