import discord


class Embed(discord.Embed):
    @classmethod
    def Success(cls, title: str, description: str):
        embed = discord.Embed(description=description, color=discord.Color.green())
        embed.set_author(
            name=title, icon_url=discord.PartialEmoji(name="Success", id=1004762059981983754, animated=False).url
        )
        return embed
