from .wallet import WalletManagement
from .item_store import ItemStore


class Economy(WalletManagement, ItemStore):
    """Economy commands, the 'start' command to get started."""


async def setup(bot):
    await bot.add_cog(Economy(bot))
