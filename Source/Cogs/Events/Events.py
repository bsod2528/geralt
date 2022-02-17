import os
import time
import aiohttp
import asyncpg
import disnake
import colorama as COLOUR

from disnake.ext import commands
from disnake.webhook.async_ import Webhook

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot    =   bot
    
    COLOUR.init()

    @commands.Cog.listener()
    async def on_guild_join(self, GUILD):
        """Sends a Webhook upon joining a guild"""
        self.session    =   aiohttp.ClientSession()
        self.WEBHOOK    =   Webhook.from_url(os.getenv("JOINLOG"), session = self.session)
        
        try:
            await self.bot.DB.execute(f"INSERT INTO guild_info (id, name, owner_id) VALUES ($1, $2, $3)", GUILD.id, GUILD.name, GUILD.owner_id)
            print(COLOUR.Fore.LIGHTYELLOW_EX + f"-> {time.strftime('%c', time.gmtime())} - Logged in {GUILD}'s details." + COLOUR.Style.RESET_ALL)
        except asyncpg.UniqueViolationError:
            print(COLOUR.Fore.LIGHTCYAN_EX + f"-> {time.strftime('%c', time.gmtime())} - {GUILD}'s information has already been logged in." + COLOUR.Style.RESET_ALL)

        JOIN_EMB    =   disnake.Embed(
            title   =   f":scroll: I Joined {GUILD.name}",
            colour  =   self.bot.colour)
        JOIN_EMB.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> General Information :",
            value   =   f"> **<:ReplyContinued:930634770004725821> - <a:Owner:905750348457738291> Owner :** {GUILD.owner.mention} (`{GUILD.owner.id}`) \n" \
                        f"> **<:ReplyContinued:930634770004725821> - <a:Info:905750331789561856> Identification No. :** `{GUILD.id}` \n" \
                        f"> **<:Reply:930634822865547294> - <a:Verify:905748402871095336> Verification Level :** {str(GUILD.verification_level).replace('_', ' ').replace('`NONE`', '`NILL`').title()}")
        JOIN_EMB.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> Initialisation :",
            value   =   f"> **<:ReplyContinued:930634770004725821> - <a:Woo:905754435379163176> Made On :** {self.bot.DT(GUILD.created_at)} \n" \
                        f"> **<:Reply:930634822865547294> - <a:WumpusVibe:905457020575031358> I Joined :** {self.bot.DT(disnake.utils.utcnow())}",
            inline  =   False)                
        JOIN_EMB.timestamp  =   disnake.utils.utcnow()
        JOIN_EMB.set_thumbnail(url = GUILD.icon.url)
        await self.WEBHOOK.send(embed = JOIN_EMB)
        await self.session.close()
    
    @commands.Cog.listener()
    async def on_guild_remove(self, GUILD):
        """Sends a Webhook upon being removed from a guild"""
        self.session    =   aiohttp.ClientSession()
        self.WEBHOOK    =   Webhook.from_url(os.getenv("LEAVELOG"), session = self.session)
        
        LEAVE_EMB    =   disnake.Embed(
            title   =   f":scroll: I Left {GUILD.name}",
            colour  =   disnake.Colour.from_rgb(255, 97, 142))
        LEAVE_EMB.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> General Information :",
            value   =   f"> **<:ReplyContinued:930634770004725821> - <a:Owner:905750348457738291> Owner :** {GUILD.owner.mention} (`{GUILD.owner.id}`) \n" \
                        f"> **<:ReplyContinued:930634770004725821> - <a:Info:905750331789561856> Identification No. :** `{GUILD.id}` \n" \
                        f"> **<:Reply:930634822865547294> - <a:Verify:905748402871095336> Verification Level :** {str(GUILD.verification_level).replace('_', ' ').replace('`NONE`', '`NILL`').title()} \n")
        LEAVE_EMB.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> Initialisation :",
            value   =   f"> **<:ReplyContinued:930634770004725821> - <a:Woo:905754435379163176> Made On :** {self.bot.DT(GUILD.created_at)} \n" \
                        f"> **<:Reply:930634822865547294> - <a:PAIN:939876989655994488> I Left :** {self.bot.DT(disnake.utils.utcnow())}",
            inline  =   False)                
        LEAVE_EMB.timestamp  =   disnake.utils.utcnow()
        LEAVE_EMB.set_thumbnail(url = GUILD.icon.url)
        await self.WEBHOOK.send(embed = LEAVE_EMB)
        await self.session.close()

    @commands.Cog.listener()
    async def on_slash_command_error(self, interaction : disnake.ApplicationCommandInteraction, error : commands.CommandError):
        self.session    =   aiohttp.ClientSession()
        self.WEBHOOK    =   Webhook.from_url(os.getenv("ERROR"), session = self.session)
        ERROR_EMB   =   disnake.Embed(
            title       =   f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED",
            description = f"```py\n{error}\n```<:Reply:930634822865547294> **Occurance :** {self.bot.DT(disnake.utils.utcnow())}",
            colour      = 0x2F3136)
        await interaction.response.send_message(embed = ERROR_EMB, ephemeral = True)
        return await self.WEBHOOK.send(embed = ERROR_EMB)

def setup(bot):
    bot.add_cog(Events(bot))