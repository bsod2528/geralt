import io
import json
import typing
from click import command
import disnake  

from typing import Optional
from disnake.ext import commands

import Source.Kernel.Utilities.Crucial as CRUCIAL

class Slash(commands.Cog):
    def __init__(self, bot):
        self.bot    =   bot
    
    @commands.slash_command(
        name        =   "ping",
        description =   "Simply ping them for fun.")
    async def ping(self, user : disnake.Member, interaction : disnake.ApplicationCommandInteraction):
        await interaction.response.send_message(f"{user.mention} you have been ponged by : **{interaction.author}**", ephemeral = False)

    @commands.slash_command(
        name        =   "bonk",
        description =   "Simply bonk them for fun.")
    async def ping(self, user : disnake.Member, interaction : disnake.ApplicationCommandInteraction):
        await interaction.response.send_message(f"{user.mention} you have been <:Bonked:934033408106057738> by : **{interaction.author}**", ephemeral = False)
    
    @commands.slash_command(
        name        =   "uptime",
        description =   "Get the uptime of me :)")
    async def ping(self, interaction : disnake.ApplicationCommandInteraction):
        await interaction.response.send_message(content = f"I have been up since <:GeraltRightArrow:904740634982760459> {self.bot.DT(self.bot.uptime, style = 'F')}\nThats about : {self.bot.DT(self.bot.uptime, style = 'R')}", ephemeral = True)

    @commands.slash_command(
        name        =   "as",
        description =   "Send a webhook as another user.")
    async def mimic(self, user : disnake.Member, *, message : str, interaction : disnake.ApplicationCommandInteraction):
        WBHK = await CRUCIAL.FETCH_WEBHOOK(interaction.channel)
        thread = disnake.utils.MISSING
        if isinstance(interaction.channel, disnake.Thread):
            thread = interaction.channel
        await WBHK.send(
            message, 
            avatar_url  =   user.display_avatar.url, 
            username    =   user.display_name, 
            thread      =   thread)
        await interaction.response.send_message(f"Done **{interaction.author}** <:NanoTick:925271358735257651>", ephemeral = True)
    
    @commands.slash_command(
        name        =   "die",
        description =   "Sends the bot to eternal sleep")
    @commands.is_owner()
    async def sleep(self, interaction : disnake.ApplicationCommandInteraction):
        await interaction.response.send_message(content = f"Okay **{interaction.author}** - I shall go to eternal sleep <:rooContemplateExistence:919902906839339018>", ephemeral = True)
        await self.bot.close()

def setup(bot):
    bot.add_cog(Slash(bot))