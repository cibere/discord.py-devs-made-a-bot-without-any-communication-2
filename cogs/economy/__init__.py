from .wallet import WalletManagement


class Economy(WalletManagement):
    """Economy commands, the 'start' command to get started."""


async def setup(bot):
    await bot.add_cog(Economy(bot))
