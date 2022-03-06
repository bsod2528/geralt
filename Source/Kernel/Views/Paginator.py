import discord

from discord import ButtonStyle

import Source.Kernel.Views.Interface as Interface

# Class for paginator using buttons. Button style and label has been inspired from RoboDanny [Discord.py Bot] by "Danny aka Rapptz" -> Github Profile
class Paginator(discord.ui.View):
    def __init__(self, bot, ctx, EMBEDS : list[discord.Embed]):
        super().__init__(timeout = 60)
        self.bot        =   bot
        self.CTX        =   ctx
        self.TOTAL      =   len(EMBEDS)
        self.EMBED      :   list[discord.Embed] =   EMBEDS
        self.CURRENT    =   0

        if self.TOTAL >= 1:
            self.LEFT.disabled = True
            self.MAX_LEFT.disabled = True

    @discord.ui.button(label = "<<", style = ButtonStyle.gray, custom_id = "<<")
    async def MAX_LEFT(self, BUTTON : discord.ui.button, INTERACTION : discord.Interaction, disabled : bool = True):
        self.CURRENT    =   0
        self.LEFT.disabled = True
        BUTTON.disabled = True
        
        if self.TOTAL >= 1:
            self.RIGHT.disabled = False
            self.MAX_RIGHT.disabled = False
        else:
            self.RIGHT.disabled = True
            self.MAX_RIGHT.disabled = True

        await INTERACTION.response.edit_message(embed = self.EMBED[self.CURRENT], view = self)
    
    @discord.ui.button(label = "<", style = ButtonStyle.blurple, custom_id = "<")
    async def LEFT(self, BUTTON : discord.ui.button, INTERACTION : discord.Interaction, disabled : bool = True):
        self.CURRENT    -=  1
        
        if self.TOTAL >= 1:
            self.MAX_RIGHT.disabled = False
            self.RIGHT.disabled = False
        else:
            self.MAX_RIGHT.disabled = True
            self.RIGHT.disabled = True

        if self.CURRENT <= 0:
            self.CURRENT = 0
            self.MAX_LEFT.disabled = True
            BUTTON.disabled = True
        else:
            self.MAX_LEFT.disabled = False
            BUTTON.disabled = False

        await INTERACTION.response.edit_message(embed = self.EMBED[self.CURRENT], view = BUTTON.view)
    
    @discord.ui.button(label = ">", style = ButtonStyle.blurple, custom_id = ">")
    async def RIGHT(self, BUTTON : discord.ui.button, INTERACTION : discord.Interaction, disabled : bool = True):
        self.CURRENT    +=  1

        if self.CURRENT >= self.TOTAL - 1:
            self.CURRENT = self.TOTAL - 1
            BUTTON.disabled = True
            self.MAX_RIGHT.disabled = True

        if len(self.EMBED) >= 1:
            self.MAX_LEFT.disabled = False
            self.LEFT.disabled = False
        else:
            self.LEFT.disabled = True
            self.MAX_LEFT.disabled = True

        await INTERACTION.response.edit_message(embed = self.EMBED[self.CURRENT], view = BUTTON.view)
    
    @discord.ui.button(label = ">>", style = ButtonStyle.gray, custom_id = ">>")
    async def MAX_RIGHT(self, BUTTON : discord.ui.button, INTERACTION : discord.Interaction, disabled : bool = False):
        self.CURRENT    =   self.TOTAL - 1
        
        BUTTON.disabled = True
        self.RIGHT.disabled = True

        if self.TOTAL >= 1:
            self.MAX_LEFT.disabled = False
            self.LEFT.disabled = False
        else:
            self.MAX_LEFT.disabled = True
            self.LEFT.disabled = True
        
        await INTERACTION.response.edit_message(embed = self.EMBED[self.CURRENT], view = BUTTON.view)

    @discord.ui.button(label = "Exit", style = ButtonStyle.danger, custom_id = "Delete")
    async def DELETE(self, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
        await INTERACTION.message.delete()     
    
    async def SEND(self, ctx):
        self.message    =   await ctx.reply(embed = self.EMBED[0], view = self, mention_author = False)
        return self.message
    
    async def on_timeout(self) -> None:
        for View in self.children:
            View.disabled = True
            await self.message.edit(view = self)

    async def interaction_check(self, INTERACTION : discord.Interaction) -> bool:
            if INTERACTION.user == self.CTX.author:
                return True
            await INTERACTION.response.send_message(content = f"{Interface.PAIN}", ephemeral = True)    