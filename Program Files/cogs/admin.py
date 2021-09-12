import os
import sys
import asyncio
import discord
import datetime
from discord.enums import InteractionType
from discord.ext import commands
from discord.ext.commands import bot, converter
from discord.ext.commands.core import command, is_owner
from discord.interactions import Interaction
class Admin(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    def av(ctx):
        return ctx.author.id == 750979369001811982 , 760823877034573864

#---unload cog---#
    @commands.command()
    @commands.check(av)
    async def unload(self, ctx, *, cog : str):
        try:
            self.bot.unload_extension(cog)
        except Exception as e:
            await ctx.send(f'**`ERROR:`**{type(e).__name__} - {e}')
        else:
            await ctx.send(f'**`Done`**')

#---load cog---#
    @commands.command()
    @commands.check(av)
    async def load(self, ctx, *, cog : str):
        try:
            self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(f'**`ERROR:`**{type(e).__name__} - {e}')
        else:
            await ctx.send(f'**`Done`**')

#---jishaku---#
    @commands.command(decription = 'Its in Admin, why you run it. Bruh')
    @commands.check(av)
    async def loadjsk(self, ctx):
        async with ctx.typing():
            self.bot.load_extension('jishaku')
            await asyncio.sleep(0.5)
    @loadjsk.error
    async def loadjsk_error(self, ctx, error):
        async with ctx.typing():
            await asyncio.sleep(0.5)
        await ctx.send(f'{ctx.message.author.mention} Man, you are not allowed for this command <:linuskill:886606006761717760>')

#---shutdown---#
    @commands.command(aliases=['close'])
    @commands.is_owner()
    async def die(self, ctx):
        async with ctx.typing():
            await asyncio.sleep(0.5)
        emb = discord.Embed(
            title = 'Gonna Kill my Self',
            description = f'Geralt is now going to die. Bye {ctx.message.author.mention} <a:pepedie:877054002599182397>',
            color = ctx.author.color)
        emb.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await ctx.send(embed = emb)
        await self.bot.close()
        await emb.add_reaction('🔪')
            
    @die.error
    async def die_error(self, ctx, error):
        async with ctx.typing():
            await asyncio.sleep(0.5)
        emb = discord.Embed(
            title = '<:linuskill:886606006761717760>',
            description = f'{ctx.message.author.mention} Well well, you think you can be more cool by shutting me down eh? SUFFER!',
            color = ctx.author.color) 
        emb.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await ctx.send(embed = emb)    

#---toggle---#
    @commands.command(name="toggle", description="Enable or disable a command!", alias = ['tg'])
    @commands.check(av)
    @commands.is_owner()
    async def toggle(self, ctx, *, command):
        command = self.bot.get_command(command)

        if command is None:
            emb = discord.Embed(
                title = 'ERROR', 
                description = 'I cant find a command with that name!', 
                color = ctx.author.color)
            emb.timestamp = datetime.datetime.now(datetime.timezone.utc)
            async with ctx.typing():
                await asyncio.sleep(0.5)
            await ctx.send(embed=emb)

        elif ctx.command == command:
            emb = discord.Embed(
                title = 'ERROR', 
                description = 'You cannot disable this command.', 
                color =ctx.author.color)
            emb.timestamp = datetime.datetime.now(datetime.timezone.utc)
            async with ctx.typing():
                await asyncio.sleep(0.5)
            await ctx.send(embed=emb)

        else:
            command.enabled = not command.enabled
            ternary = "enabled" if command.enabled else "disabled"
            emb = discord.Embed(
                title = 'Toggle',
                description = f'I have {ternary} {command.qualified_name} for you!',
                color = ctx.author.color)
            emb.timestamp = datetime.datetime.now(datetime.timezone.utc)
            async with ctx.typing():
                await asyncio.sleep(0.5)
            await ctx.send(embed=emb)


def setup(bot):
    bot.add_cog(Admin(bot))