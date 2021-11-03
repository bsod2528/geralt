import json
import discord 
import random
import asyncio
import datetime
from discord.ext import commands

class Information(commands.Cog):
    
    """Get information regarding server members"""

    def __init__(self, bot):
        self.bot = bot
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)
        self.color = 0x2F3136
        self.emote = json.load(open('Program Files\Emotes.json'))

    @commands.command(
        name = 'avatar',
        aliases = ['pfp'],
        help = f'```ini\n[ Syntax : .gavatar [member mention/id] ]\n```\n>>> **USE :** Gets the Avatar of a user or you!\n**AKA :** `.gpfp`',
        brief = 'See other members pfps enlarged')
    async def avatar(self, ctx, *, user : discord.Member = None):
        emb = discord.Embed(
            color = self.color)
        user = user or ctx.author
        avatar = user.display_avatar.with_static_format('png')
        emb.set_author(
            name = f'PFP of - {str(user)}', 
            url = avatar)
        emb.set_image(url = avatar)
        emb.timestamp = self.timestamp
        await ctx.reply(embed = emb, mention_author = False)


def setup(bot):
    bot.add_cog(Information(bot))