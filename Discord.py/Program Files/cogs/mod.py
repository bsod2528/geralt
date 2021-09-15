from datetime import datetime
from sqlite3.dbapi2 import Timestamp
import discord
from discord import utils
import random
import asyncio
import datetime 
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

    def is_it_me(ctx):
        return ctx.author.id == 750979369001811982 , 760823877034573864

#---yeet---#
    @commands.command(description = 'Yeet User from Server')
    @commands.has_guild_permissions(administrator = True)
    @commands.check(is_it_me)
    async def yeet(self, ctx, member : discord.Member, *, reason = None, alias = ['kick']):
        async with ctx.typing():        
            await asyncio.sleep(0.5)
            await ctx.send(f'**{member}** has been yeeted by **{ctx.message.author.mention}** from the server. <a:die:877059852306886696>')
        await member.kick(reason = reason)
#---yeet error---#
    @yeet.error
    async def yeet_error(self, ctx, error):
        if isinstance(error, commands.BotMissingPermissions)        :
            async with ctx.typing():
                await asyncio.sleep(0.5)
            emb = discord.Embed(
                title = 'No Perms for Me',
                description = f'{ctx.message.author.mention} I - <:leave:882101241067474984>',
                color = ctx.author.color)
            emb.timestamp = datetime.datetime.now(datetime.timezone.utc)                
            await ctx.send(embed = emb)
        else:
            async with ctx.typing():
                await asyncio.sleep(0.5)
            emb = discord.Embed(
                title = 'No Perms for You',
                description = f'{ctx.message.author.mention} <:tf:877056779131953173> You dont have perms',
                color = ctx.author.color)
            emb.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed = emb)
            
#---ban---#
    @commands.command(description = 'Let the Ban Hammer speak for its self')
    @commands.has_guild_permissions(administrator = True)
    @commands.has_permissions(ban_members = True)
    @commands.check(is_it_me)
    async def ban(self, ctx, member : discord.Member, *, reason = None):
        async with ctx.typing():
            await asyncio.sleep(0.5)
        await ctx.send(f'Ban Hammer has spoken on **{member}** from the server. <a:pepeban:877057982133833748> ')
        await member.ban(reason = reason)
        
#---ban error---#
    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.BotMissingPermissions):
            async with ctx.typing():
                await asyncio.sleep(0.5)
            emb = discord.Embed(
                title = 'No Perms for Me',
                description = f'{ctx.message.author.mention} I - <:leave:882101241067474984>',
                color = ctx.author.color)
            emb.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed = emb)
        else:
            async with ctx.typing():
                await asyncio.sleep(0.5)
            emb = discord.Embed(
                title = 'No Perms for You',
                description = f'{ctx.message.author.mention} <:tf:877056779131953173> You dont have perms',
                color = ctx.author.color)
            emb.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed = emb)
            
#---unban---#
    @commands.command(decription = 'You bring the devil back into your server.')
    @commands.check(is_it_me)
    @commands.has_guild_permissions(administrator = True, ban_members = True)
    async def unban(self, ctx, *, member):
        async with ctx.typing():
            await asyncio.sleep(0.5)
        banned_user = await ctx.guild.bans()
        member_name, member_discriminator = member.split('#')

        for ban_entry in banned_user:
            user = ban_entry.user

            if (user.name, user.discriminator) --(member_name, member_discriminator):
                await ctx.guild.unban(user)
                await ctx.send(f'Sucessfully unbanned {user.Mention}')
                return

#---purge---#
    @commands.command(description = 'Deletes messages on any scale.')
    @commands.has_permissions(administrator = True, manage_messages = True)
    async def clear(self, ctx, amount: int):
        async with ctx.typing():
            await asyncio.sleep(0.5)
            await ctx.channel.purge(limit = amount)
        await ctx.send(f'Sucessesfuly purged {amount} messages. Peace {ctx.message.author.mention}')
#---purge error---#
    @clear.error
    async def clear_error(self, ctx, error):
        async with ctx.typing():
            await asyncio.sleep(0.5)
        emb = discord.Embed(
            title = 'Purge Undergone',
            description = f'{ctx.message.author.mention} How many messages do you want to delete. Specify particularly.',
            color = ctx.author.color
        )
        emb.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await ctx.send(embed = emb)

def setup(bot): 
    bot.add_cog(Mod(bot))