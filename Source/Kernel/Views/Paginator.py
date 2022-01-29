import disnake

from disnake import ButtonStyle

import Source.Kernel.Views.Interface as Interface

# Class for paginator using buttons. Button style and label has been inspired from RoboDanny [Discord.py Bot] by "Danny aka Rapptz" -> Github Profile
class Paginator(disnake.ui.View):
    def __init__(self, ctx, EMBEDS : list[disnake.Embed]):
        super().__init__()
        self.CTX        =   ctx
        self.TOTAL      =   len(EMBEDS)
        self.EMBED      :   list[disnake.Embed] =   EMBEDS
        self.CURRENT    =   0

        if self.TOTAL >= 1:
            self.LEFT.disabled = True
            self.MAX_LEFT.disabled = True

    @disnake.ui.button(label = "<<", style = ButtonStyle.gray)
    async def MAX_LEFT(self, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction, disabled : bool = True):
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
    
    @disnake.ui.button(label = "<", style = ButtonStyle.blurple)
    async def LEFT(self, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction, disabled : bool = True):
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
    
    @disnake.ui.button(label = ">", style = ButtonStyle.blurple)
    async def RIGHT(self, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction, disabled : bool = True):
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
    
    @disnake.ui.button(label = ">>", style = ButtonStyle.gray)
    async def MAX_RIGHT(self, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction, disabled : bool = False):
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

    @disnake.ui.button(label = "Exit", style = ButtonStyle.danger)
    async def DELETE(self, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction):
        await INTERACTION.message.delete()

    async def interaction_check(self, INTERACTION : disnake.Interaction) -> bool:
            if INTERACTION.user == self.CTX.author:
                return True
            await INTERACTION.response.send_message(content = f"{Interface.PAIN}", ephemeral = True)