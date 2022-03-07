import time
import aiohttp
import asyncpg
import discord
import colorama as colour

from discord.ext import commands
from discord.webhook.async_ import Webhook

from __main__ import CONFIG

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot    =   bot
        
    colour.init()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Sends a Webhook upon joining a guild"""
        self.session    =   aiohttp.ClientSession()
        self.wbhk       =   Webhook.from_url(CONFIG.get("JOINLOG"), session = self.session)
        
        try:
            await self.bot.db.execute(f"INSERT INTO guild_info (id, name, owner_id) VALUES ($1, $2, $3)", guild.id, guild.name, guild.owner_id)
            print(colour.Fore.LIGHTYELLOW_EX + f"-> {time.strftime('%c', time.gmtime())} - Logged in {guild}'s details." + colour.Style.RESET_ALL)
        except asyncpg.UniqueViolationError:
            print(colour.Fore.LIGHTCYAN_EX + f"-> {time.strftime('%c', time.gmtime())} - {guild}'s information has already been logged in." + colour.Style.RESET_ALL)

        join_emb    =   discord.Embed(
            title   =   f":scroll: I Joined {guild.name}",
            colour  =   self.bot.colour)
        join_emb.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> General Information :",
            value   =   f"> **<:ReplyContinued:930634770004725821> - <a:Owner:905750348457738291> Owner :** {guild.owner.mention} (`{guild.owner.id}`) \n" \
                        f"> **<:ReplyContinued:930634770004725821> - <a:Info:905750331789561856> Identification No. :** `{guild.id}` \n" \
                        f"> **<:Reply:930634822865547294> - <a:Verify:905748402871095336> Verification Level :** {str(guild.verification_level).replace('_', ' ').replace('`None`', '`Nill`').title()}")
        join_emb.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> Initialisation :",
            value   =   f"> **<:ReplyContinued:930634770004725821> - <a:Woo:905754435379163176> Made On :** {self.bot.datetime(guild.created_at)} \n" \
                        f"> **<:Reply:930634822865547294> - <a:WumpusVibe:905457020575031358> I Joined :** {self.bot.datetime(discord.utils.utcnow())}",
            inline  =   False)                
        join_emb.timestamp  =   discord.utils.utcnow()
        join_emb.set_thumbnail(url = guild.icon.url)
        await self.wbhk.send(embed = join_emb)
        await self.session.close()
    
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """Sends a Webhook upon being removed from a guild"""
        self.session    =   aiohttp.ClientSession()
        self.wbhk       =   Webhook.from_url(CONFIG.get("LEAVELOG"), session = self.session)
        
        leave_emb    =   discord.Embed(
            title   =   f":scroll: I Left {guild.name}",
            colour  =   discord.Colour.from_rgb(255, 97, 142))
        leave_emb.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> General Information :",
            value   =   f"> **<:ReplyContinued:930634770004725821> - <a:Owner:905750348457738291> Owner :** {guild.owner.mention} (`{guild.owner.id}`) \n" \
                        f"> **<:ReplyContinued:930634770004725821> - <a:Info:905750331789561856> Identification No. :** `{guild.id}` \n" \
                        f"> **<:Reply:930634822865547294> - <a:Verify:905748402871095336> Verification Level :** {str(guild.verification_level).replace('_', ' ').replace('`None`', '`Nill`').title()} \n")
        leave_emb.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> Initialisation :",
            value   =   f"> **<:ReplyContinued:930634770004725821> - <a:Woo:905754435379163176> Made On :** {self.bot.datetime(guild.created_at)} \n" \
                        f"> **<:Reply:930634822865547294> - <a:PAIN:939876989655994488> I Left :** {self.bot.datetime(discord.utils.utcnow())}",
            inline  =   False)                
        leave_emb.timestamp  =   discord.utils.utcnow()
        leave_emb.set_thumbnail(url = guild.icon.url)
        await self.wbhk.send(embed = leave_emb)
        await self.session.close()

def setup(bot):
    bot.add_cog(Events(bot))