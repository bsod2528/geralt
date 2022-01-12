import time
import discord
import asyncio

from discord.ext import commands
from discord.ext.commands import bot

from __main__ import EMOTE
from Kernel.Utilities.Interface import Info

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name    =   "ping",
        aliases =   ["pong"],
        brief   =   "You ping Me",
        help    =   "Get proper latency timings of the bot.")
    async def ping(self, ctx):
        PING    =   []
        
        # Latency for TYPING
        TYPING_START = time.perf_counter()
        async with ctx.typing():
            await asyncio.sleep(0.5)
        TYPING_END = time.perf_counter()
        TYPING_PING = (TYPING_END - TYPING_START) * 1000

        # Latency for DATABASE
        START_DB    =   time.perf_counter()
        await self.bot.DB.fetch("SELECT 1")
        END_DB  =   time.perf_counter()
        DB_PING =   (END_DB - START_DB) * 1000
        PING.append(DB_PING)

        # Latency for Discord API
        WEBSOCKET_PING   =   self.bot.latency * 1000
        PING.append(WEBSOCKET_PING)

        PING_EMB = discord.Embed(
            title = "__My Latency__",
            description =   f"{EMOTE['Needed']['RG']} - Typing : `{round(TYPING_PING, 1)} ms`\n"
                            f"{EMOTE['Needed']['RG']} - Discord API : `{WEBSOCKET_PING:,.0f} ms`\n"
                            f"{EMOTE['Needed']['R']} - Database : `{round(DB_PING, 1)} ms`",
            colour = self.bot.colour)
        PING_EMB.timestamp = self.bot.Timestamp
        await ctx.reply(embed = PING_EMB, mention_author = False)
    
    # Huge shoutout to @Zeus432 [ Github User ID ] for the idea of implementing buttons for System Usage [ PSUTIl ] and Latest Commits on Github :)
    @commands.command(
        name    =   "info",
        aliases =   ["about"],
        brief   =   "Get info on me",
        help    =   "Receive full information regarding me.")
    async def info(self, ctx):
        INFO_EMB    =   discord.Embed(
            title = "__Geralt : Da Bot__",
            url = self.bot.PFP,
            description =   f"Hi <a:Waves:920726389869641748> [**Geralt**](https://bsod2528.github.io/Posts/Geralt) Da Bot ! I am an **open source** bot made for fun as my dev has no idea what he's doing. I'm currently under reconstruction, so I suck at the moment [ continued after costruction ]. I'm made by **BSOD#3375**\n\nCame to Discord on __<t:{round(ctx.me.created_at.timestamp())}:D>__\nYou can check out my [**Github**](https://github.com/BSOD2528/Geralt) or by clicking the `Github Commits` button :D ",
            colour = self.bot.colour)
        INFO_EMB.add_field(
            name = "General Statistics :",
            value = f"**<:ReplyContinued:930634770004725821> - Base Language :** <:WinPython:898614277018124308> __Python 3.10.0__\n**<:Reply:930634822865547294> - Base Library :** <a:Discord:930855436670889994> [**Discord.py**](https://github.com/Rapptz/discord.py)")
        INFO_EMB.set_thumbnail(url = self.bot.PFP)
        async with ctx.typing():
            await asyncio.sleep(0.5)
        INFO_EMB.timestamp = self.bot.Timestamp
        await ctx.reply(embed = INFO_EMB, mention_author = False, view = Info(ctx, bot))
  
def setup(bot):
    bot.add_cog(Misc(bot))
