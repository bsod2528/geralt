import os
import sys
import asyncio
import discord
import datetime
import logging
import json
from discord import user
from discord import channel
from discord.enums import InteractionType
from discord.ext import commands
from discord.ext.commands import bot, converter
from discord.ext.commands.core import command, is_owner
from discord.interactions import Interaction
from logging import exception

class Admin(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    def av(ctx):
        return ctx.author.id == 750979369001811982 , 760823877034573864

#---unload cog---#
    @commands.command(
        name = 'unload', 
        help = f'```ini\n[ Syntax : .gunload cogs.<cog name> ]\n```\n>>> __***Bot Owner command, dont even think about running this***__\n**USE :** Unload Cogs in a fraction of a second!\n**AKA :** No aliases present ;)', 
        brief = 'Unload dem!')
    @commands.check(av)
    @commands.is_owner()
    async def unload(self, ctx, *, cog : str):
        try:
            self.bot.unload_extension(cog)
        except Exception as e:
            await ctx.reply(f'**`ERROR:`**{type(e).__name__} - {e}')
        else:
            await ctx.reply(f'**`Done`**')

#---load cog---#
    @commands.command(
        name = 'load', 
        help = f'```ini\n[ Syntax : .gload cogs.<cog name> ]\n```\n>>> __***Bot Owner command, dont even think about running this***__\n**USE :** Load Cogs faster than Mcqueen!\n**AKA :** No aliases present ;)', 
        brief = 'Load em')
    @commands.check(av)
    @commands.is_owner()
    async def load(self, ctx, *, cog : str):
        try:
            self.bot.load_extension(cog)
        except Exception as e:
            await ctx.reply(f'**`ERROR:`**{type(e).__name__} - {e}')
        else:
            await ctx.reply(f'**`Done`**')

#---jishaku---#
    @commands.command(
        name = 'loadjsk', 
        help = f'```ini\n[ Syntax : .gloadjsk ]\n```\n>>> __***Bot Owner command, dont even think about running this***__\n**USE :** Loads Jishaku as a COG\n**AKA :** No aliases present ;)')
    @commands.is_owner()
    async def loadjsk(self, ctx):
        emote = json.load(open('D:\AV\PC\Coding\Discord Bot\Geralt\Discord.py\Program Files\emote.json'))
        async with ctx.typing():
            self.bot.load_extension('jishaku')
            await asyncio.sleep(0.5)
        await ctx.reply(f'Done! JISHAKU now loaded up for {emote["areyousure"]} ... Well for running the commands you dumbo')

#---shutdown---#
    @commands.command(
        name = 'die',
        aliases = ['snap'],
        help = f'```ini\n[ Syntax : .gdie ]\n```\n>>> __***Bot Owner command, dont even think about running this***__\n**USE :** If my dev uses it, I Die\n**AKA :** `.gsnap`')
    @commands.is_owner()
    async def die(self, ctx):
        emote = json.load(open('D:\AV\PC\Coding\Discord Bot\Geralt\Discord.py\Program Files\emote.json'))
        async with ctx.typing():
            await asyncio.sleep(0.5)
        await ctx.reply(f'Imma kill ma self. Bye! {emote["panda"]["snap"]}')
        await self.bot.close()  
    

#---toggle---#
    @commands.command(
        name="toggle", 
        help = f'```ini\n[ Syntax : .gtoggle <command name> ]\n```\n>>> __***Bot Owner command, dont even think about running this***__\n**USE :** Enable or disable a command!\n**AKA :** `.gtog`', 
        aliases = ['tog'])
    @commands.is_owner()
    async def toggle(self, ctx, *, command):
        emote = json.load(open('D:\AV\PC\Coding\Discord Bot\Geralt\Discord.py\Program Files\emote.json'))
        command = self.bot.get_command(command)

        if command is None:
            async with ctx.typing():
                await asyncio.sleep(0.5)
            await ctx.reply(f'{emote["frog"]["worryrun"]} I cant find a command with that name!')

        elif ctx.command == command:
            async with ctx.typing():
                await asyncio.sleep(0.5)
            await ctx.reply(f'{emote["anxiety"]["trigger"]}You cannot disable this command')

        else:
            command.enabled = not command.enabled
            ternary = "enabled" if command.enabled else "disabled"
            async with ctx.typing():
                await asyncio.sleep(0.5)
            await ctx.reply(f'I have {ternary} {command.qualified_name} for you! {emote["peep"]["prayage"]}',)

#---channel send---#
    #commands.command(hidden = True)
    #commands.is_owner()
    #async def cs(self, ctx, *, args):
    #   channel = self.bot.get_channel(args)
    #   await channel.send(f'<:sdemote:886958983775129600>')

def setup(bot):
    bot.add_cog(Admin(bot))