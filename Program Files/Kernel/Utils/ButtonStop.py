import discord
from discord.enums import ButtonStyle
from discord.ext import commands

class SelfStop(discord.ui.View):
    
    @discord.ui.button(label = 'Delete', style = ButtonStyle.blurple, emoji = '\U0001f5d1')
    async def close(self, button : discord.ui.button, interaction : discord.Interaction, *args) -> bool:
        await interaction.message.delete()