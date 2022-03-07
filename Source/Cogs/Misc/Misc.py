import io
import time
import json
import typing
import urllib
import aiohttp
import discord
import asyncio
import humanize

from discord.ext import commands
from discord.enums import ButtonStyle
from discord.webhook.async_ import Webhook

from __main__ import CONFIG
import Source.Kernel.Views.Interface as Interface

class Misc(commands.Cog):
    """Miscellaneous Commands"""
    def __init__(self, bot):
        self.bot = bot
        self.session    =   aiohttp.ClientSession()
        self.bug        =   Webhook.from_url(CONFIG.get("BUG"), session = self.session)
        self.report     =   Webhook.from_url(CONFIG.get("REPORT"), session = self.session)

    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.command(
        name    =   "ping",
        aliases =   ["pong"],
        brief   =   "You ping Me")
    async def ping(self, ctx : commands.context):
        """Get proper latency timings of the bot."""

        # Latency for typing
        typing_start = time.perf_counter()
        async with ctx.typing():
            await asyncio.sleep(0.5)
        typing_end = time.perf_counter()
        typing_ping = (typing_end - typing_start) * 1000

        # Latency with the database
        start_db    =   time.perf_counter()
        await self.bot.db.fetch("SELECT 1")
        end_db  =   time.perf_counter()
        db_ping =   (end_db - start_db) * 1000

        # Latency for Discord Api
        websocket_ping   =   self.bot.latency * 1000

        ping_emb = discord.Embed(
            title = "__ My Latencies : __",
            description =   f"""```prolog\n> PostgreSQL     : {round(db_ping, 1)} ms
> Discord API    : {websocket_ping:,.0f} ms
> Message Typing : {round(typing_ping, 1)} ms\n```""",
            colour = self.bot.colour)
        ping_emb.timestamp = discord.utils.utcnow()
        await ctx.reply(embed = ping_emb, mention_author = False)
    
    # Huge shoutout to @Zeus432 [ Github User ID ] for the idea of implementing buttons for System Usage [ PSUTIl ] and Latest Commits on Github :)
    @commands.command(
        name    =   "info",
        aliases =   ["about"],
        brief   =   "Get info on me")
    async def info(self, ctx : commands.context):
        """Receive full information regarding me."""
        info_emb    =   discord.Embed(
            title = "<:WinGIT:898591166864441345> __Geralt : Da Bot__",
            url = self.bot.pfp,
            description =   f"Hi <a:Waves:920726389869641748> I am [**Geralt**](https://bsod2528.github.io/Posts/Geralt) Da Bot ! I am an **open source** bot made for fun as my dev has no idea what he's doing. I'm currently under reconstruction, so I suck at the moment [ continued after construction ]. I'm made by **BSOD#2528**\n\n>>> <:GeraltRightArrow:904740634982760459> Came to Discord on __<t:{round(ctx.me.created_at.timestamp())}:D>__\n<:GeraltRightArrow:904740634982760459> You can check out my [**Dashboard**](https://bsod2528.github.io/Posts/Geralt) or by clicking the `Dashboard` button :D ",
            colour = self.bot.colour)
        info_emb.add_field(
            name = "General Statistics :",
            value = f"**<:ReplyContinued:930634770004725821> - Guilds In :** `{len(self.bot.guilds)}`" \
                    f"\n**<:Reply:930634822865547294> - Channels In :** `{sum(1 for x in self.bot.get_all_channels())}`")
        info_emb.add_field(
            name = "Program Statistics :",
            value = f"**<:ReplyContinued:930634770004725821> - Base Language :** <:WinPython:898614277018124308> [**Python 3.10.0**](https://www.python.org/downloads/release/python-3100/)" \
                    f"\n**<:Reply:930634822865547294> - Base Library :** <a:Discord:930855436670889994> [**Discord.py**](https://github.com/DisnakeDev/disnake)")
        info_emb.set_thumbnail(url = self.bot.pfp)
        async with ctx.typing():
            await asyncio.sleep(0.5)
        info_emb.timestamp = discord.utils.utcnow()
        await ctx.reply(embed = info_emb, mention_author = False, view = Interface.Info(self.bot, ctx))

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
    async def bug(self, ctx, *, bug : str):
        """Send a bug to the dev if you find any."""
        bug_info    =   f"- Reported By   :   {ctx.author} / {ctx.author.id}\n" \
                        f"- @ Guild       :   {ctx.guild} / {ctx.guild.id}\n" \
                        f"- @ Channel     :   {ctx.channel} / {ctx.channel.id}"
        bug_emb =   discord.Embed(
            title   =   "Bug Reported",
            description =   f"```yaml\n{bug_info}\n```",
            colour  =   0x2F3136)
        bug_emb.add_field(
            name    =   "Below Holds the Bug",
            value   =   f"```css\n[ {bug} ]\n```")
        bug_emb.timestamp   =   discord.utils.utcnow()
        
        async def yes(ui : discord.ui.View, button : discord.ui.button, interaction : discord.Interaction):
            if interaction.user != ctx.author:
                return await interaction.response.send_message(content = f"{Interface.PAIN}", ephemeral = True)
            for view in ui.children:
                    view.disabled   =   True
                    view.style      =   ButtonStyle.blurple
            try:
                await self.bug.send(embed = bug_emb)
                await self.bug.send("||  Break Point  ||")
            except Exception as exception:
                await ui.response.edit(content = f"Couldn't send your report due to : **{exception}**", view = ui)
            else:
                await ui.response.edit(content = "Successfully sent your `Bug Report` to the Developer <:RavenPray:914410353155244073>", view = ui, allowed_mentions = self.bot.mentions)
            ui.stop()
        
        async def no(ui : discord.ui.View, button : discord.ui.button, interaction : discord.Interaction):
            if interaction.user != ctx.author:
                return await interaction.response.send_message(content = f"{Interface.PAIN}", ephemeral = True)
            for view in ui.children:
                    view.disabled   =   True
                    view.style  =   ButtonStyle.blurple
            await ui.response.edit(content = "Seems like you don't want to send your `Bug Report` to the dev.\nNot my problem <:AkkoHmm:907105376523153458>", view = None, allowed_mentions = self.bot.mentions)
        Interface.Confirmation.response    = await ctx.reply("Are you sure you want to send your `Bug Report` <:Sus:916955986953113630>", view = Interface.Confirmation(ctx, yes, no), allowed_mentions = self.bot.mentions)

    @report.command(
        name    =   "feedback",
        aliases =   ["fb"],
        brief   =   "Send your feeback")
    async def feedback(self, ctx : commands.context, *, feedback : str):
        """Send a feedback to the dev if you find any."""
        fb_info =   f"- Sent By       :   {ctx.author} / {ctx.author.id}\n" \
                    f"- @ Guild       :   {ctx.guild} / {ctx.guild.id}\n" \
                    f"- @ Channel     :   {ctx.channel} / {ctx.channel.id}"
        fb_emb  =   discord.Embed(
            title   =   "Feedback Entered",
            description =   f"```yaml\n{fb_info}\n```\n[**Jump to Feedback**]({ctx.message.jump_url})\n",
            colour  =   0x2F3136)
        fb_emb.add_field(
            name    =   "Below Holds the Feedback",
            value   =   f"```css\n{feedback}\n```")
        fb_emb.timestamp   =   discord.utils.utcnow()
        
        async def yes(ui : discord.ui.View, button : discord.ui.button, interaction : discord.Interaction):
            if interaction.user != ctx.author:
                return await interaction.response.send_message(content = f"{Interface.PAIN}", ephemeral = True)
            for view in ui.children:
                    view.disabled   =   True
                    view.style      =   ButtonStyle.blurple
            try:
                await self.report.send(embed = fb_emb)
                await self.report.send("||  Break Point  ||")
            except Exception as EXCEPT:
                await ui.response.edit(content = f"Couldn't send your feedback due to : **{EXCEPT}**", view = ui)
            else:
                await ui.response.edit(content = f"Successfully sent your `Feedback` to the Developer <:RavenPray:914410353155244073>", view = ui, allowed_mentions = self.bot.mentions)
            ui.stop()
        
        async def no(ui : discord.ui.View, button : discord.ui.button, interaction : discord.Interaction):
            if interaction.user != ctx.author:
                return await interaction.response.send_message(content = f"{Interface.PAIN}", ephemeral = True)
            for view in ui.children:
                    view.disabled   =   True
                    view.style      =   ButtonStyle.blurple
            await ui.response.edit("Seems like you don't want to send your `Feeback` to the dev.\nNot my problem <:AkkoHmm:907105376523153458>", view = None, allowed_mentions = self.bot.mentions)
        Interface.Confirmation.response    = await ctx.reply("Are you sure you want to send your `Feedback` <:Sus:916955986953113630>", view = Interface.Confirmation(ctx, yes, no), allowed_mentions = self.bot.mentions)

    @commands.command(
        name    =   "json",
        aliases =   ["raw"],
        brief   =   "Sends JSON Data")
    async def json(self, ctx : commands.context, message : typing.Optional[discord.Message]):
        """Get the JSON Data for a message."""
        message :   discord.Message = getattr(ctx.message.reference, "resolved", message)
        if not message:
            return await ctx.reply(f"**{ctx.author}**, please reply to the message or enter the message id if you want to see the raw message on.")
        try:
            message_data    =   await self.bot.http.get_message(message.channel.id, message.id)
        except discord.HTTPException as HTTP:
            raise commands.BadArgument("OOP, there's an error, please try again")
        json_data       =   json.dumps(message_data, indent = 4)
        await ctx.trigger_typing()
        await ctx.reply(f"Here you go <:NanoTick:925271358735257651>", file = discord.File(io.StringIO(json_data), filename = "Message-Raw-Data.json"), allowed_mentions = self.bot.mentions)

    @commands.cooldown(3, 5, commands.BucketType.user)
    @commands.command(
        name    =   "uptime",
        aliases =   ["ut"],
        brief   =   "Returns Uptime")
    async def uptime(self, ctx : commands.context):
        """Sends my uptime -- how long I've been online for"""
        time    =   discord.utils.utcnow() - self.bot.uptime
        await ctx.trigger_typing()
        await ctx.reply(f"<:GeraltRightArrow:904740634982760459> I have been `online` for -\n>>> <:ReplyContinued:930634770004725821> - Exactly : {humanize.precisedelta(time)}\n<:Reply:930634822865547294> - Roughly Since : {self.bot.datetime(self.bot.uptime, style = 'R')} <a:CoffeeSip:907110027951742996>")

    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.command(
        name    =   "google",
        aliases =   ["g", "web"],
        brief   =   "Search Google")
    async def web(self, ctx : commands.context, *, query : str):
        """Search Google for anything"""
        api_key     =   CONFIG.get("SEARCH")
        cx          =   CONFIG.get("ENGINE")
        query_time  =   []
        session = aiohttp.ClientSession()
        
        given_query     =   urllib.parse.quote(query)
        ping_start      =   time.perf_counter()
        result_url      =   f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={cx}&q={given_query}&safe=active"
        api_results     =   await session.get(result_url)
        ping_end        =   time.perf_counter()
        queried_ping   =   (ping_end - ping_start) * 1000
        query_time.append(queried_ping)

        if api_results.status    ==  200:
            json_value  =   await api_results.json()
        else:
            return await ctx.reply(f"{ctx.author.mention} No results found.```\n{query}```")

        web_result_list =   []
        serial_no       =   1
        for values in json_value["items"]:
            url         = values["link"]
            title       = values["title"]
            web_result_list.append(f"> **{serial_no}). [{title}]({url})**\n")
            serial_no   +=  1
        
        web_emb =   discord.Embed(
            description =  f"".join(results for results in web_result_list),
            colour  =   self.bot.colour)
        web_emb.timestamp   =   discord.utils.utcnow()
        web_emb.set_author(name = f"{ctx.author}'s Query Results :", icon_url = ctx.author.display_avatar.url)
        web_emb.set_footer(text = f"Queried in : {round(queried_ping)} ms")
        await ctx.reply(embed = web_emb, allowed_mentions = self.bot.mentions)
        await session.close()

    @commands.command(
        name    =   "invite",
        aliases =   ["inv"],
        brief   =   "Get Invite Link")
    async def invite(self, ctx : commands.context):
        invite_emb  =   discord.Embed(
            colour  =   self.bot.colour)
        invite_emb.add_field(
            name    =   "Permissions :",
            value   =   f"> <:replycont:875990141427146772> **-** [**Administrator Permissions**](https://discord.com/api/oauth2/authorize?client_id=873204919593730119&permissions=8&scope=bot+applications.commands)\n" \
                        f"> <:replycont:875990141427146772> **-** [**Moderator Permissions**](https://discord.com/api/oauth2/authorize?client_id=873204919593730119&permissions=1116922503303&scope=bot+applications.commands)\n" \
                        f"> <:Reply:930634822865547294> **-** [**Regular Permissions**](https://discord.com/api/oauth2/authorize?client_id=873204919593730119&permissions=67420289&scope=bot+applications.commands)")
        invite_emb.set_thumbnail(url    =   self.bot.PFP)
        invite_emb.set_author(name = f"{ctx.message.author} : Invite Links Below", icon_url = ctx.author.display_avatar.url)
        invite_emb.timestamp = discord.utils.utcnow()
        await ctx.reply(embed = invite_emb, mention_author = False)

def setup(bot):
    bot.add_cog(Misc(bot))