import os
import webbrowser
import time
import random
from discord import channel, mentions, user
import requests
import discord
import random
import sys
import asyncio
import datetime
from discord import DMChannel
from discord import Spotify
from discord import message
from discord.enums import ContentFilter, T
from discord.errors import Forbidden
from discord.ext import commands
from discord.ext import tasks
from discord.ext.commands import context, has_permissions, MissingPermissions
from discord.utils import find
from itertools import cycle
from discord.ext.commands.core import command, has_guild_permissions, has_permissions
from jishaku.cog import Jishaku
from jishaku.cog import STANDARD_FEATURES, OPTIONAL_FEATURES
from jishaku.features.python import PythonFeature
from jishaku.features.root_command import RootCommand
from jishaku.features.baseclass import Feature
from googleapiclient.discovery import build

#---prefix---#      
bot = commands.Bot(command_prefix = '.g', status = discord.Status.idle, activity = discord.Game(name = '.ghelp ; i hate my self'))

#---checks---#
def av(ctx):
    return ctx.author.id == 750979369001811982 , 760823877034573864

#---help command---#
class EmbedHelp(commands.HelpCommand):
    def get_command_signature(self, command):
        return '{0.qualified_name} {0.signature}'.format(command)

    async def send_bot_help(self, mapping):
        emb = discord.Embed(
            title = 'Geralt is Here to Help', 
            color = 0x9b59b6)
        description = self.context.bot.description
        if description:
            emb.description = description

        for cog, commands in mapping.items():
            name = 'Essential' if cog is None else cog.qualified_name
            filtered = await self.filter_commands(commands, sort = True)
            if filtered:
                value = '\u2002'.join(c.name for c in commands)
                if cog and cog.description:
                    value = '{0}\n{1}'.format(cog.description, value)

                emb.add_field(
                    name = name, 
                    value = value,
                    inline = False)
                emb.set_footer(text = 'Run ginfo for website and join our [support server](https://discord.gg/JXEu2AcV5Y)')
                emb.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await self.get_destination().send(embed = emb)
    
    async def send_group_help(self, group):
        embed = discord.Embed(title = group.qualified_name)
        if group.help:
            embed.description = group.help

        if isinstance(group, commands.Group):
            filtered = await self.filter_commands(group.commands, sort=True)
            for command in filtered:
                embed.add_field(name=self.get_command_signature(command), value=command.short_doc or '...', inline=False)
        await self.get_destination().send(embed=embed)
    send_command_help = send_group_help
bot.help_command = EmbedHelp()

#---button---#
class GeraltLink(discord.ui.View):
    def __init__(self):
        super().__init__()
        url = f'https://bsod2528.wixsite.com/geralt'
        self.add_item(discord.ui.Button(label = 'GERALT | HOME', url = url, emoji = '<:me:881174571804409886>'))
@bot.command(hidden = True)
async def info(ctx :commands.Context):
    await ctx.send(f'Here is my website. Please check it out to learn more !', view = GeraltLink())

#---boot---#
@bot.event
async def on_ready():
    print('Geralt is ready for action')

#---cogs setup---#
for filename in os.listdir('D:\AV\PC\Coding\Discord Bot\Geralt\Program Files\cogs'):
    if filename.endswith('.py'):    
            bot.load_extension(f'cogs.{filename[:-3]}')

#---read dms---#
received = 880128519110262794
@bot.event
async def on_message(message: discord.Message):
    channel = bot.get_channel(received)
    if message.guild is None and not message.author.bot:
        emb = discord.Embed(
            title = 'My DMs',
            description = f'{message.author.mention} sent ➜ \n " *{message.content}* "' ,
            color = 0x9b59b6)
        emb.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await channel.send(embed = emb)
    await bot.process_commands(message)

bot.run('ODczMjA0OTE5NTkzNzMwMTE5.YQ1BdA.HNr2ruzPri47HN3NWoVQ_wkdi54')
