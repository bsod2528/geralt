import discord


class BaseEmbed(discord.Embed):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.timestamp = discord.utils.utcnow()

    def __repr__(self) -> str:
        return "<geralt.BaseEmbed>"
