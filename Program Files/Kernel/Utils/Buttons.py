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
    def __init__(self, bot):
        super().__init__()

        @discord.ui.button(label = 'Delete', style = ButtonStyle.blurple, emoji = '\U0001f5d1')
        async def close(self, button : discord.ui.button, interaction : discord.Interaction, *args) -> bool:
            await interaction.message.delete()

    async def interaction_check(self, interaction:discord.Interaction):
        inter_check = discord.Embed(
            color = self.color,
            title = 'SIKE !!',
            description = f'<@{interaction.user.id}> ! <@{self.help.context.author.id}> INVOKED THE COMMAND, NOT YOU IDIOT !! ',
            timestamp = self.help.context.message.created_at
        )
        await interaction.response.send_message(embed = inter_check, ephemeral = True)
        return False
        
class ExceptionButton(discord.ui.View):
    def __init__(self, bot):
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
    
class Die(discord.ui.View):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
    
    @discord.ui.button(style = ButtonStyle.green, emoji = '<:WinSuccess:898571689623978054>')
    async def yes(self, button : discord.ui.button, interaction : discord.Interaction, *args) -> bool:
        await interaction.response.send_message('Okay, Ill die FFS!', ephemeral = True)
        await self.bot.close()

    @discord.ui.button(style = ButtonStyle.red, emoji = '<:WinCritical:898571769114406942>')
    async def no(self, button : discord.ui.button, interaction : discord.Interaction):
        await interaction.response.send_message('Thank you for sparing me!', ephemeral = True)
        self.stop()

class Nitro(discord.ui.View):
    
    @discord.ui.button(label = '\u2001\u2001\u2001\u2001\u2001\u2001\u2001\u2001\u2001\u2001\u2001\u2001Claim\u2001\u2001\u2001\u2001\u2001\u2001\u2001\u2001\u2001\u2001\u2001', style = ButtonStyle.green)
    async def nitro(self, button : discord.ui.button, interaction : discord.Interaction, *args) -> bool:
        await interaction.response.send_message(content = '__**RICKROLLED AT 60FPS 1080P RESOLUTION ! SUCK ON THAT HAA !**__\n\nhttps://imgur.com/NQinKJB', ephemeral = True)
