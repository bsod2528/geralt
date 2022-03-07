from click import command
import discord

from discord import ButtonStyle
from discord.ext import commands

import Source.Kernel.Views.Interface as Interface

# Sub - class for paginator using buttons. Button style and label has been inspired from RoboDanny [Discord.py Bot] by "Danny aka Rapptz" -> Github Profile
class Paginator(discord.ui.View):
    def __init__(self, bot, ctx : commands.context, embeds : list[discord.Embed]):
        super().__init__()
        self.bot        =   bot
        self.ctx        =   ctx
        self.total      =   len(embeds)
        self.embeds     :   list[discord.Embed] =   embeds
        self.current    =   0

        if self.total >= 1:
            self.left.disabled = True
            self.max_left.disabled = True

    @discord.ui.button(label = "<<", style = ButtonStyle.gray, custom_id = "<<")
    async def max_left(self, button : discord.ui.button, interaction : discord.Interaction, disabled : bool = True):
        self.current    =   0
        self.left.disabled = True
        button.disabled = True
        
        if self.total >= 1:
            self.right.disabled = False
            self.max_right.disabled = False
        else:
            self.right.disabled = True
            self.max_right.disabled = True

        await interaction.response.edit_message(embed = self.embeds[self.current], view = self)
    
    @discord.ui.button(label = "<", style = ButtonStyle.blurple, custom_id = "<")
    async def left(self, button : discord.ui.button, interaction : discord.Interaction, disabled : bool = True):
        self.current    -=  1
        
        if self.total >= 1:
            self.max_right.disabled = False
            self.right.disabled = False
        else:
            self.max_right.disabled = True
            self.right.disabled = True

        if self.current <= 0:
            self.current = 0
            self.max_left.disabled = True
            button.disabled = True
        else:
            self.max_left.disabled = False
            button.disabled = False

        await interaction.response.edit_message(embed = self.embeds[self.current], view = button.view)
    
    @discord.ui.button(label = ">", style = ButtonStyle.blurple, custom_id = ">")
    async def right(self, button : discord.ui.button, interaction : discord.Interaction, disabled : bool = True):
        self.current    +=  1

        if self.current >= self.total - 1:
            self.current = self.total - 1
            button.disabled = True
            self.max_right.disabled = True

        if len(self.embeds) >= 1:
            self.max_left.disabled = False
            self.left.disabled = False
        else:
            self.left.disabled = True
            self.max_left.disabled = True

        await interaction.response.edit_message(embed = self.embeds[self.current], view = button.view)
    
    @discord.ui.button(label = ">>", style = ButtonStyle.gray, custom_id = ">>")
    async def max_right(self, button : discord.ui.button, interaction : discord.Interaction, disabled : bool = False):
        self.current    =   self.total - 1
        
        button.disabled = True
        self.right.disabled = True

        if self.total >= 1:
            self.max_left.disabled = False
            self.left.disabled = False
        else:
            self.max_left.disabled = True
            self.left.disabled = True
        
        await interaction.response.edit_message(embed = self.embeds[self.current], view = button.view)

    @discord.ui.button(label = "Exit", style = ButtonStyle.danger, custom_id = "Delete")
    async def delete(self, button : discord.ui.button, interaction : discord.Interaction):
        await interaction.message.delete()     
    
    async def send(self, ctx):
        self.message    =   await ctx.reply(embed = self.embeds[0], view = self, mention_author = False)
        return self.message

    async def interaction_check(self, interaction : discord.Interaction) -> bool:
            if interaction.user == self.ctx.author:
                return True
            await interaction.response.send_message(content = f"{Interface.PAIN}", ephemeral = True)    