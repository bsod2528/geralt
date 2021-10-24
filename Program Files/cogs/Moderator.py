from datetime import datetime
from sqlite3.dbapi2 import Timestamp
import discord
from discord import utils
import random
import asyncio
import datetime 
import json
import asyncpg
from discord import client
from discord import user
from discord.abc import _Overwrites
from discord.channel import DMChannel
from discord.ext import commands
from discord.ext.commands import cog
from discord.ext.commands.core import command, is_owner

class Mod(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.color = discord.Color.from_rgb(117, 128, 219)
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)
        self.json = json.load(open('Emotes.json'))   

    def is_it_me(ctx):
        return ctx.author.id == 750979369001811982 , 760823877034573864

    @commands.command(
        name = 'yeet', 
        help = f'```ini\n[ Syntax : .gyeet <user> ]\n```\n>>> **USE :** Yeet pests out of your server\n**AKA :** No aliases present ;)', 
        brief = 'Yeet User from Server')
    @commands.has_guild_permissions(kick_members = True)
    @commands.check(is_it_me)
    async def yeet(self, ctx, member : discord.Member, *, reason = None, alias = ['kick']):
        emote = self.json
        async with ctx.typing():        
            await asyncio.sleep(0.5)
        await member.kick(reason = reason)
        await ctx.reply(f'**{member}** has been yeeted by **{ctx.message.author.mention}** from the server. {emote["peep"]["walk"]}')
        
    @commands.command(
        name = 'ban', 
        help = f'```ini\n[ Syntax : .gban <user> ]\n```\n>>> **USE :** Get rid of toxic peeps forever by banning them!\n**AKA :** No aliases present ;)', 
        brief = 'Let the Ban Hammer speak for its self')
    @commands.guild_only()
    @commands.has_permissions(ban_members = True)
    async def ban(self, ctx, member: discord.Member, *, reason = None):
        emote = self.json
        async with ctx.typing():
            await asyncio.sleep(0.5)
        await member.ban(reason = reason)
        await ctx.reply(f'Ban Hammer has spoken on **{member}** from the server.')
        await ctx.send(f'{emote["peep"]["ban"]}')
        
    @commands.command(
        name = 'clear', 
        help = f'```ini\n[ Syntax : .gclear <no. of messages> ]\n```\n>>> **USE :** Having a Genocide Plan! Delete messages on a mass scale!\n**AKA :** No aliases present ;)', 
        brief = 'Deletes messages on any scale.')
    @commands.has_permissions(manage_messages = True)
    async def clear(self, ctx, amount: int):
        await ctx.channel.purge(limit = amount)

def setup(bot): 
    bot.add_cog(Mod(bot))