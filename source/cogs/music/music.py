import discord
import wavelink

from discord.ext import commands
from wavelink.ext import spotify

from ...kernel.subclasses.bot import Geralt
from ...kernel.subclasses.embed import BaseEmbed
from ...kernel.subclasses.context import GeraltContext
from ...kernel.subclasses.wavelink_player import GeraltPlayer


class Music(commands.Cog):
    def __init__(self, bot: Geralt):
        self.bot: Geralt = bot

    @property
    def emote(self) -> str:
        return "\U0001f3b9"

    @commands.command(
        name="join",
        brief="Join a vc",
        aliases=["connect"])
    async def join(self, ctx: GeraltContext):
        """Joins Voice Channel"""
        await ctx.author.voice.channel.connect(cls=GeraltPlayer)
        await ctx.add_nanotick()
