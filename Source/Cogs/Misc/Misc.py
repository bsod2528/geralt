import io
import time
import json
import typing
import aiohttp
import disnake
import asyncio

from disnake.ext import commands
from disnake.ext.commands import bot
from disnake.webhook.async_ import Webhook

from __main__ import KERNEL
import Source.Kernel.Views.Interface as Interface

class Misc(commands.Cog):
    """Miscellaneous Commands"""
    def __init__(self, bot):
        self.bot = bot
        self.session    =   aiohttp.ClientSession()
        self.BUG        =   Webhook.from_url(KERNEL["Tokens"]["Bug"], session = self.session)
        self.REPORT     =   Webhook.from_url(KERNEL["Tokens"]["Report"], session = self.session)

    @commands.command(
        name    =   "ping",
        aliases =   ["pong"],
        brief   =   "You ping Me")
    async def ping(self, ctx):
        """Get proper latency timings of the bot."""
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

        # Latency for Disnake API
        WEBSOCKET_PING   =   self.bot.latency * 1000
        PING.append(WEBSOCKET_PING)

        PING_EMB = disnake.Embed(
            title = "__ My Latencies : __",
            description =   f"""```prolog\n> PostGreSQL     : {round(DB_PING, 1)} ms
> Discord API    : {WEBSOCKET_PING:,.0f} ms
> Message Typing : {round(TYPING_PING, 1)} ms\n```""",
            colour = self.bot.colour)
        PING_EMB.timestamp = disnake.utils.utcnow()
        await ctx.reply(embed = PING_EMB, mention_author = False)
    
    # Huge shoutout to @Zeus432 [ Github User ID ] for the idea of implementing buttons for System Usage [ PSUTIl ] and Latest Commits on Github :)
    @commands.command(
        name    =   "info",
        aliases =   ["about"],
        brief   =   "Get info on me")
    async def info(self, ctx):
        """Receive full information regarding me."""
        INFO_EMB    =   disnake.Embed(
            title = "__Geralt : Da Bot__",
            url = self.bot.PFP,
            description =   f"Hi <a:Waves:920726389869641748> I am [**Geralt**](https://bsod2528.github.io/Posts/Geralt) Da Bot ! I am an **open source** bot made for fun as my dev has no idea what he's doing. I'm currently under reconstruction, so I suck at the moment [ continued after construction ]. I'm made by **BSOD#3375**\n\nCame to Discord on __<t:{round(ctx.me.created_at.timestamp())}:D>__\nYou can check out my [**Github**](https://github.com/BSOD2528/Geralt) or by clicking the `Github Commits` button :D ",
            colour = self.bot.colour)
        INFO_EMB.add_field(
            name = "General Statistics :",
            value = f"**<:ReplyContinued:930634770004725821> - Guilds In :** `{len(self.bot.guilds)}`" \
                    f"\n**<:Reply:930634822865547294> - Channels In :** `{sum(1 for x in self.bot.get_all_channels())}`")
        INFO_EMB.add_field(
            name = "Program Statistics :",
            value = f"**<:ReplyContinued:930634770004725821> - Base Language :** <:WinPython:898614277018124308> [**Python 3.10.0**](https://www.python.org/downloads/release/python-3100/)" \
                    f"\n**<:Reply:930634822865547294> - Base Library :** <a:Discord:930855436670889994> [**Disnake**](https://github.com/DisnakeDev/disnake)")
        INFO_EMB.set_thumbnail(url = self.bot.PFP)
        async with ctx.typing():
            await asyncio.sleep(0.5)
        INFO_EMB.timestamp = disnake.utils.utcnow()
        await ctx.reply(embed = INFO_EMB, mention_author = False, view = Interface.Info(ctx, bot))

    @commands.group(
        name    =   "report",
        aliases =   ["r"],
        brief   =   "Report Something")
    @commands.guild_only()
    async def report(self, ctx):
        """Send a message to the Developer regarding a bug or a request."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)
    
    @report.command(
        name    =   "bug",
        brief   =   "Report a bug")
    async def bug(self, ctx, *, BUG):
        """Send a bug to the dev if you find any."""
        BUG_INFO    =   f"- Reported By   :   {ctx.author} / {ctx.author.id}\n" \
                        f"- @ Guild       :   {ctx.guild} / {ctx.guild.id}\n" \
                        f"- @ Channel     :   {ctx.channel} / {ctx.channel.id}"
        BUG_EMB =   disnake.Embed(
            title   =   "Bug Reported",
            description =   f"```yaml\n{BUG_INFO}\n```",
            colour  =   0x2F3136)
        BUG_EMB.add_field(
            name    =   "Below Holds the Bug",
            value   =   f"```css\n[ {BUG} ]\n```")
        BUG_EMB.timestamp   =   disnake.utils.utcnow()
        
        async def YES(UI : disnake.ui.View, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction):
            if INTERACTION.user != ctx.author:
                await INTERACTION.response.send_message(content = f"{Interface.PAIN}", ephemeral = True)
                return
            try:
                await self.BUG.send(embed = BUG_EMB)
            except Exception as EXCEPT:
                await UI.response.edit(content = f"Couldn't send your report due to : **{EXCEPT}**")
                await UI.response.add_reaction("<:WinCritical:898571769114406942>")
            else:
                await UI.response.edit(content = "Successfully sent your `Bug Report` to the Developer <:RavenPray:914410353155244073>", view = None, allowed_mentions = self.bot.Mention)
                await UI.response.add_reaction("<:WinSuccess:898571689623978054>")
            UI.stop()
        
        async def NO(UI : disnake.ui.View, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction):
            if INTERACTION.user != ctx.author:
                await INTERACTION.response.send_message(content = f"{Interface.PAIN}", ephemeral = True)
                return
            await UI.response.edit(content = "Seems like you don't want to send your `Bug Report` to the dev.\nNot my problem <:AkkoHmm:907105376523153458>", view = None, allowed_mentions = self.bot.Mention)
        Interface.Confirmation.response    = await ctx.reply("Are you sure you want to send your `Bug Report` <:Sus:916955986953113630>", view = Interface.Confirmation(YES, NO), allowed_mentions = self.bot.Mention)

    @report.command(
        name    =   "feedback",
        aliases =   ["fb"],
        brief   =   "Send your feeback")
    async def feedback(self, ctx, *, FEEDBACK):
        """Send a feedback to the dev if you find any."""
        FB_INFO =   f"- Sent By       :   {ctx.author} / {ctx.author.id}\n" \
                    f"- @ Guild       :   {ctx.guild} / {ctx.guild.id}\n" \
                    f"- @ Channel     :   {ctx.channel} / {ctx.channel.id}"
        FB_EMB  =   disnake.Embed(
            title   =   "Feedback Entered",
            description =   f"```yaml\n{FB_INFO}\n```",
            colour  =   0x2F3136)
        FB_EMB.add_field(
            name    =   "Below Holds the Feedback",
            value   =   f"```json\n{FEEDBACK}\n```")
        FB_EMB.timestamp   =   disnake.utils.utcnow()
        
        async def YES(UI : disnake.ui.View, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction):
            if INTERACTION.user != ctx.author:
                await INTERACTION.response.send_message(content = f"{Interface.PAIN}", ephemeral = True)
                return
            try:
                await self.REPORT.send(embed = FB_EMB)
            except Exception as EXCEPT:
                await UI.response.edit(content = f"Couldn't send your feedback due to : **{EXCEPT}**")
                await UI.response.add_reaction("<:WinCritical:898571769114406942>")
            else:
                await UI.response.edit(content = f"Successfully sent your `Feedback` to the Developer <:RavenPray:914410353155244073>", view = None, allowed_mentions = self.bot.Mention)
                await UI.response.add_reaction("<:WinSuccess:898571689623978054>")
            UI.stop()
        
        async def NO(UI : disnake.ui.View, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction):
            if INTERACTION.user != ctx.author:
                await INTERACTION.response.send_message(content = f"{Interface.PAIN}", ephemeral = True)
                return
            await UI.response.edit("Seems like you don't want to send your `Feeback` to the dev.\nNot my problem <:AkkoHmm:907105376523153458>", view = None, allowed_mentions = self.bot.Mention)
        Interface.Confirmation.response    = await ctx.reply("Are you sure you want to send your `Feedback` <:Sus:916955986953113630>", view = Interface.Confirmation(YES, NO), allowed_mentions = self.bot.Mention)

    @commands.command(
        name    =   "json",
        aliases =   ["raw"],
        brief   =   "Sends JSON Data")
    async def json(self, ctx, MESSAGE : typing.Optional[disnake.Message]):
        """Get the JSON Data for a message."""
        MESSAGE :   disnake.Message = getattr(ctx.message.reference, "resolved", MESSAGE)
        if not MESSAGE:
            await ctx.reply(f"**{ctx.author}**, please reply to the message you want to see the raw message on.")
        try:
            MESSAGE_DATA    =   await self.bot.http.get_message(MESSAGE.channel.id, MESSAGE.id)
        except disnake.HTTPException as HTTP:
            raise commands.BadArgument("OOP, there's an error, please try again")
        JSON_DATA       =   json.dumps(MESSAGE_DATA, indent = 4)
        await ctx.trigger_typing()
        await ctx.reply(f"Here you go <:NanoTick:925271358735257651>", file = disnake.File(io.StringIO(JSON_DATA), filename = "Message-Raw-Data.json"), allowed_mentions = self.bot.Mention)
    
def setup(bot):
    bot.add_cog(Misc(bot))