import io
from typing import Tuple
import discord
import asyncio
import traceback
import json
from discord import interactions
from discord import client
from discord import ui
from discord import emoji
from discord.components import Button
from discord.enums import T, ButtonStyle
from discord.ext import commands
from discord.ext.commands import cog
from discord.ext.commands.cog import Cog
from discord.ui.button import B, button
from discord.user import BU

class SelfStop(discord.ui.View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx

    @discord.ui.button(style = ButtonStyle.blurple, emoji = '<a:Trash:906004182463569961>')
    async def close(self, button : discord.ui.button, interaction : discord.Interaction, *args) -> bool:
            await interaction.message.delete()

    async def interaction_check(self, interaction : discord.Interaction):
        if interaction.user.id == self.ctx.author.id:
            return True
        inter_check = discord.Embed(
            color = 0x2F3136,
            title = 'SIKE !!',
            description = f'<@{interaction.user.id}> **! YOU DIDNT INVOKE THE COMMAND !!** ')
        await interaction.response.send_message(embed = inter_check, ephemeral = True)
        return False
        
class ExceptionButton(discord.ui.View):
    def __init__(self, ctx):
        super().__init__()
        
    @discord.ui.button(label = 'Exception', style = ButtonStyle.danger)
    async def exception(self, button : discord.ui.button, interaction : discord.Interaction, *args) -> bool:
            await interaction.response.send_message(f'```py\n{Exception.__class__.__name__} --> {Exception}\n```', ephemeral = True)

    @discord.ui.button(label = 'Delete', style = ButtonStyle.blurple)
    async def close(self, button : discord.ui.Button, interaction : discord.Interaction, *args) -> bool:
        await interaction.response.send_message('Deleting', ephemeral = True)
        await interaction.message.delete()

    @discord.ui.button(label = 'Traceback', style = ButtonStyle.danger)
    async def traceback(self, button : discord.ui.button, interaction : discord.Interaction, *args) -> bool:
        stdout = io.StringIO()
        value = stdout.getvalue()
        await interaction.response.send_message(f'```py\n{value}{traceback.format_exc()}\n```', ephemeral = True)
    
    async def interaction_check(self, interaction : discord.Interaction):
        if interaction.user.id == self.ctx.author.id:
            return True
        inter_check = discord.Embed(
            color = 0x2F3136,
            title = 'SIKE !!',
            description = f'<@{interaction.user.id}> **! THIS IS AN BOT OWNER INTERACTION, NOT YOURS IDIOT !!** ')
        await interaction.response.send_message(embed = inter_check, ephemeral = True)
        return False
    
class Die(discord.ui.View):
    def __init__(self, ctx, bot):
        super().__init__()
        self.bot = bot
        self.ctx = ctx
    
    @discord.ui.button(style = ButtonStyle.green, emoji = '<:WinSuccess:898571689623978054>')
    async def yes(self, button : discord.ui.button, interaction : discord.Interaction, *args) -> bool:
        await interaction.response.send_message('Okay, Ill die FFS!', ephemeral = True)
        await self.bot.close()

    @discord.ui.button(style = ButtonStyle.red, emoji = '<:WinCritical:898571769114406942>')
    async def no(self, button : discord.ui.button, interaction : discord.Interaction):
        await interaction.response.send_message('Thank you for sparing me!', ephemeral = True)

    async def interaction_check(self, interaction : discord.Interaction):
        if interaction.user == self.ctx.author:
            return True
        inter_check = discord.Embed(
            color = 0x2F3136,
            title = 'SIKE !!',
            description = f'<@{interaction.user.id}> **! THIS IS A OWNER CMD BEACH !!** ')
        await interaction.response.send_message(embed = inter_check, ephemeral = True)
        return False

class Nitro(discord.ui.View):
    def __init__(self, ctx, member : discord.Member = None):
        super().__init__(timeout = 60)
        self.ctx = ctx
        self.member = member or ctx.author

    @discord.ui.button(label = '\u2001\u2001\u2001\u2001\u2001\u2001\u2001\u2001\u2001\u2001\u2001\u2001Claim\u2001\u2001\u2001\u2001\u2001\u2001\u2001\u2001\u2001\u2001\u2001', style = ButtonStyle.green)
    async def nitro(self, button : discord.ui.button, interaction : discord.Interaction, *args) -> bool:
        await interaction.response.send_message(content = '__**RICKROLLED AT 60FPS 1080P RESOLUTION ! SUCK ON THAT HAA !**__\n\nhttps://imgur.com/NQinKJB', ephemeral = True)

    async def interaction_check(self, interaction : discord.Interaction):
        if interaction.id == self.member.id:
            return True
        inter_check = discord.Embed(
            color = 0x2F3136,
            title = 'SIKE !!',
            description = f'<@{interaction.user.id}> **! THAT NITRO ~~`IS`~~ FOR YOU !!** ')
        await interaction.response.send_message(embed = inter_check, ephemeral = True)
        return False