import disnake
import aiohttp
import datetime

from disnake.ext import commands

class Moderation(commands.Cog):
    """Moderation Commands"""
    def __init__(self, bot):
        self.bot    =   bot

def setup(bot):
    bot.add_cog(Moderation(bot))