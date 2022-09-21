import io
import os
import time
import json
import urllib
import aiohttp
import discord
import asyncio
import inspect
import humanize

from typing import Optional
from discord import app_commands
from discord.ext import commands

from ...cogs.help.help import GeraltHelp
from ...kernel.views.paginator import Paginator
from ...kernel.subclasses.embed import BaseEmbed
from ...kernel.views.meta import Info, Confirmation
from ...kernel.utilities.crucial import total_lines
from ...kernel.subclasses.bot import CONFIG, Geralt
from ...kernel.subclasses.context import GeraltContext


class Meta(commands.Cog):
    """Commands which don't fall under any of the cogs"""

    def __init__(self, bot: Geralt):
        self.bot: Geralt = bot
        self._original_help_command = bot.help_command
        help_command = GeraltHelp()
        help_command.cog = self
        bot.help_command = help_command

    @property
    def emote(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(
            name="Meta",
            id=905748764432662549,
            animated=True)

    @commands.hybrid_command(
        name="ping",
        brief="You ping Me",
        aliases=["pong"])
    @app_commands.checks.cooldown(2, 10)
    @commands.cooldown(2, 10, commands.BucketType.user)
    async def ping(self, ctx: GeraltContext) -> Optional[discord.Message]:
        """Get proper latency timings of the bot."""

        # Latency for typing
        typing_start = time.perf_counter()
        async with ctx.typing():
            await asyncio.sleep(0.5)
        typing_end = time.perf_counter()
        typing_ping = (typing_end - typing_start) * 1000

        # Latency with the database
        start_db = time.perf_counter()
        await self.bot.db.fetch("SELECT 1")
        end_db = time.perf_counter()
        db_ping = (end_db - start_db) * 1000

        # Latency for Discord Api
        websocket_ping = self.bot.latency * 1000

        ping_emb = BaseEmbed(
            title="__ My Latencies : __",
            colour=0x2F3136)

        if ctx.interaction:
            if ctx.author.is_on_mobile():
                ping_emb.description = f"""```yaml\n> PostgreSQL     : {round(db_ping, 1)} ms
> Discord API    : {websocket_ping:,.0f} ms\n```"""
                return await ctx.reply(embed=ping_emb, mention_author=False, ephemeral=True)
            else:
                ping_emb.description = f"""```ansi\n\x1b[0;1;37;40m > \x1b[0m \x1b[0;1;34mPostgreSQL\x1b[0m     \x1b[0;1;37;40m : \x1b[0m \x1b[0;1;31m{round(db_ping, 1)} ms\x1b[0m
\x1b[0;1;37;40m > \x1b[0m \x1b[0;1;34mDiscord API\x1b[0m    \x1b[0;1;37;40m : \x1b[0m \x1b[0;1;31m{websocket_ping:,.0f} ms\x1b[0m\n```"""
                return await ctx.reply(embed=ping_emb, mention_author=False, ephemeral=True)
        else:
            if ctx.author.is_on_mobile():
                ping_emb.description = f"""```yaml\n> PostgreSQL     : {round(db_ping, 1)} ms
> Discord API    : {websocket_ping:,.0f} ms
> Message Typing : {round(typing_ping, 1)} ms\n```"""
                await ctx.reply(embed=ping_emb, mention_author=False)
            else:
                ping_emb.description = f"""```ansi\n\x1b[0;1;37;40m > \x1b[0m \x1b[0;1;34mPostgreSQL\x1b[0m     \x1b[0;1;37;40m : \x1b[0m \x1b[0;1;31m{round(db_ping, 1)} ms\x1b[0m
\x1b[0;1;37;40m > \x1b[0m \x1b[0;1;34mDiscord API\x1b[0m    \x1b[0;1;37;40m : \x1b[0m \x1b[0;1;31m{websocket_ping:,.0f} ms\x1b[0m
\x1b[0;1;37;40m > \x1b[0m \x1b[0;1;34mMessage Typing\x1b[0m \x1b[0;1;37;40m : \x1b[0m \x1b[0;1;31m{round(typing_ping, 1)} ms\x1b[0m\n```"""
            await ctx.reply(embed=ping_emb, mention_author=False)

    # Huge shoutout to @Zeus432 [ Github User ID ] for the idea of
    # implementing buttons for System Usage [ PSUTIl ] and Latest Commits on
    # Github :)

    @commands.hybrid_command(
        name="info",
        brief="Get info on me",
        aliases=["about"])
    @commands.cooldown(2, 10, commands.BucketType.user)
    async def info(self, ctx: GeraltContext) -> Optional[discord.Message]:
        """Receive full information regarding me."""
        info_emb = BaseEmbed(
            title="<:WinGIT:898591166864441345> __Geralt : Da Bot__",
            url=ctx.me.display_avatar.url,
            description=f"Hi <a:Waves:920726389869641748> I am [**Geralt**](https://bsod2528.github.io/Posts/Geralt) Da Bot ! I am a locally hosted **open source** bot made for fun as my dev has no idea what he's doing. I'm currently under reconstruction, so I suck at the moment [ continued after construction ]. I'm made by **BSOD#0067**\n\n>>> <:GeraltRightArrow:904740634982760459> Came to Discord on <t:{round(ctx.me.created_at.timestamp())}:f>\n<:GeraltRightArrow:904740634982760459> You can check out my [**Dashboard**](https://bsod2528.github.io/Posts/Geralt) or by clicking the `Dashboard` button :D",
            colour=self.bot.colour)
        info_emb.add_field(
            name="General Statistics :",
            value=f"<:ReplyContinued:930634770004725821> ` ─ ` Guilds In : `{len(self.bot.guilds)}`"
            f"\n<:Reply:930634822865547294> ` ─ ` Channels In : `{sum(1 for x in self.bot.get_all_channels())}`")
        info_emb.add_field(
            name="Program Statistics :",
            value=f"<:ReplyContinued:930634770004725821> ` ─ ` Language : <:WinPython:898614277018124308> [**Python 3.10.5**](https://www.python.org/downloads/release/python-3100/)"
            f"\n<:Reply:930634822865547294> ` ─ ` Base Library : <a:Discord:930855436670889994> [**Discord.py**](https://github.com/DisnakeDev/disnake)")
        info_emb.set_thumbnail(url=ctx.me.display_avatar.url)
        async with ctx.typing():
            await asyncio.sleep(0.5)
        await ctx.reply(embed=info_emb, mention_author=False, view=Info(self.bot, ctx))

    @commands.hybrid_group(
        name="report",
        brief="Report Something",
        aliases=["r"],
        with_app_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def report(self, ctx: GeraltContext) -> Optional[discord.Message]:
        """Send a message to the Developer regarding a bug or a request."""
        if ctx.invoked_subcommand is None:
            await ctx.command_help()

    @report.command(
        name="bug",
        brief="Report a bug",
        with_app_command=True)
    @app_commands.checks.cooldown(1, 20)
    @app_commands.describe(bug="Something that you've found wrong with me.")
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def bug(self, ctx: GeraltContext, *, bug: str) -> Optional[discord.Message]:
        """Send a bug to the dev if you find any."""
        bug_info = f"- Reported By   :   {ctx.author} / {ctx.author.id}\n" \
                   f"- @ Guild       :   {ctx.guild} / {ctx.guild.id}\n" \
                   f"- @ Channel     :   {ctx.channel} / {ctx.channel.id}"
        bug_emb = BaseEmbed(
            title="Bug Reported",
            description=f"```yaml\n{bug_info}\n```",
            colour=0x2F3136)
        bug_emb.add_field(
            name="Below Holds the Bug",
            value=f"```css\n[ {bug} ]\n```")

        async def yes(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.button):
            for view in ui.children:
                view.disabled = True
            try:
                async with aiohttp.ClientSession() as session:
                    bug_webhook = discord.Webhook.partial(
                        id=CONFIG.get("BUG_ID"), token=CONFIG.get("BUG_TOKEN"), session=session)
                    await bug_webhook.send(embed=bug_emb)
                    await bug_webhook.send("||  Break Point  ||")
                    await session.close()
            except Exception as exception:
                await interaction.response.defer()
                await ui.response.edit(content=f"Couldn't send your report due to : **{exception}**", view=ui)
            else:
                await interaction.response.defer()
                await ui.response.edit(content="Successfully sent your `Bug Report` to the Developer <:RavenPray:914410353155244073>", view=ui, allowed_mentions=self.bot.mentions)
            ui.stop()

        async def no(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.button):
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            await ui.response.edit(content="Seems like you don't want to send your `Bug Report` to the dev.\nNot my problem <:AkkoHmm:907105376523153458>", view=None, allowed_mentions=self.bot.mentions)
        Confirmation.response = await ctx.reply("Are you sure you want to send your `Bug Report` <:Sus:916955986953113630>", view=Confirmation(ctx, yes, no), allowed_mentions=self.bot.mentions)

    @report.command(
        name="feedback",
        brief="Send your feeback",
        aliases=["fb"],
        with_app_command=True)
    @app_commands.checks.cooldown(1, 20)
    @app_commands.describe(feedback="How you feel about the user experience in general.")
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def feedback(self, ctx: GeraltContext, *, feedback: str) -> Optional[discord.Message]:
        """Send a feedback to the dev if you find any."""
        fb_info = f"- Sent By       :   {ctx.author} / {ctx.author.id}\n" \
                  f"- @ Guild       :   {ctx.guild} / {ctx.guild.id}\n" \
                  f"- @ Channel     :   {ctx.channel} / {ctx.channel.id}"
        fb_emb = BaseEmbed(
            title="Feedback Entered",
            description=f"```yaml\n{fb_info}\n```\n[**Jump to Feedback**]({ctx.message.jump_url})\n",
            colour=0x2F3136)
        fb_emb.add_field(
            name="Below Holds the Feedback",
            value=f"```css\n{feedback}\n```")

        async def yes(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.button):
            for view in ui.children:
                view.disabled = True
            try:
                async with aiohttp.ClientSession() as session:
                    feedback_webhook = discord.Webhook.partial(
                        id=CONFIG.get("FEEDBACK_ID"),
                        token=CONFIG.get("FEEDBACK_TOKEN"),
                        session=session)
                    await feedback_webhook.send(embed=fb_emb)
                    await feedback_webhook.send("||  Break Point  ||")
                    await session.close()
            except Exception as exception:
                await interaction.response.defer()
                await ui.response.edit(content=f"Couldn't send your feedback due to : **{exception}**", view=ui)
            else:
                await interaction.response.defer()
                await ui.response.edit(content=f"Successfully sent your `Feedback` to the Developer <:RavenPray:914410353155244073>", view=ui, allowed_mentions=self.bot.mentions)
            ui.stop()

        async def no(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.button):
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            await ui.response.edit("Seems like you don't want to send your `Feeback` to the dev.\nNot my problem <:AkkoHmm:907105376523153458>", view=None, allowed_mentions=self.bot.mentions)
        Confirmation.response = await ctx.reply("Are you sure you want to send your `Feedback` <:Sus:916955986953113630>", view=Confirmation(ctx, yes, no), allowed_mentions=self.bot.mentions)

    @commands.command(
        name="json",
        brief="Sends JSON Data",
        aliases=["raw"])
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def json(self, ctx: GeraltContext, message: Optional[discord.Message]) -> Optional[discord.Message]:
        """Get the JSON Data for a message."""
        message: discord.Message = getattr(
            ctx.message.reference, "resolved", message)
        if not message:
            return await ctx.reply(f"**{ctx.author}**, please \n\n` - ` reply to the message \n` - ` enter the message id \n` - ` send the message link \nif you want to see the raw message on.")
        try:
            message_data = await self.bot.http.get_message(message.channel.id, message.id)
        except discord.HTTPException as HTTP:
            raise commands.BadArgument(
                "Oop! There's an error, please try again")
        json_data = json.dumps(message_data, indent=2)
        await ctx.reply(f"Here you go <:NanoTick:925271358735257651>", file=discord.File(io.StringIO(json_data), filename="Message-Raw-Data.json"), allowed_mentions=self.bot.mentions)

    @commands.hybrid_command(
        name="uptime",
        brief="Returns Uptime",
        aliases=["ut"],
        with_app_command=True)
    @app_commands.checks.cooldown(3, 5)
    @commands.cooldown(3, 5, commands.BucketType.user)
    async def uptime(self, ctx: GeraltContext) -> Optional[discord.Message]:
        """Sends my uptime -- how long I've been online for"""
        time = discord.utils.utcnow() - self.bot.uptime
        try:
            async with ctx.typing():
                await asyncio.sleep(0.5)
        except BaseException:
            pass
        await ctx.reply(f"<:GeraltRightArrow:904740634982760459> I have been \"**online**\" for -\n>>> <:ReplyContinued:930634770004725821>` ─ ` Exactly : {humanize.precisedelta(time)}\n<:Reply:930634822865547294>` ─ ` Roughly Since : {self.bot.timestamp(self.bot.uptime, style = 'R')} ({self.bot.timestamp(self.bot.uptime, style = 'f')}) <a:CoffeeSip:907110027951742996>")

    @commands.hybrid_command(
        name="google",
        brief="Search Google",
        aliases=["g", "web"],
        with_app_command=True)
    @app_commands.checks.cooldown(2, 5)
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def web(self, ctx: GeraltContext, *, query: str) -> Optional[discord.Message]:
        """Search Google for anything"""
        cx = CONFIG.get("ENGINE")
        api_key = CONFIG.get("SEARCH")
        query_time = []
        session = aiohttp.ClientSession()

        given_query = urllib.parse.quote(query)
        ping_start = time.perf_counter()
        result_url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={cx}&q={given_query}&safe=active"
        api_results = await session.get(result_url)
        ping_end = time.perf_counter()
        queried_ping = (ping_end - ping_start) * 1000
        query_time.append(queried_ping)

        if api_results.status == 200:
            json_value = await api_results.json()
        else:
            return await ctx.reply(f"{ctx.author.mention} No results found.```\n{query}```")

        web_result_list = []
        serial_no = 0
        for values in json_value["items"]:
            serial_no += 1
            url = values["link"]
            title = values["title"]
            web_result_list.append(
                f"│ ` - ` **{serial_no}). [{title}]({url})**\n")

        web_emb = BaseEmbed(
            description=f"".join(results for results in web_result_list),
            colour=self.bot.colour)
        web_emb.set_author(
            name=f"{ctx.author}'s Query Results :",
            icon_url=ctx.author.display_avatar.url)
        web_emb.set_footer(text=f"Queried in : {round(queried_ping)} ms")
        await ctx.reply(embed=web_emb, allowed_mentions=self.bot.mentions)
        await session.close()

    @commands.hybrid_command(
        name="invite",
        brief="Get Invite Links",
        aliases=["inv"],
        with_app_command=True)
    async def invite(self, ctx: GeraltContext) -> Optional[discord.Message]:
        invite_emb = BaseEmbed(
            colour=self.bot.colour)
        invite_emb.add_field(
            name="Permissions :",
            value=f"────\n> │ ` - ` <a:WumpusVibe:905457020575031358> [**Regular Permissions**](https://discord.com/api/oauth2/authorize?client_id=873204919593730119&permissions=67420289&scope=bot+applications.commands)\n"
            f"> │ ` - ` <:ModBadge:904765450066473031> [**Moderator Permissions**](https://discord.com/api/oauth2/authorize?client_id=873204919593730119&permissions=1116922503303&scope=bot+applications.commands)\n"
            f"> │ ` - ` <a:Owner:905750348457738291> [**Administrator Permissions**](https://discord.com/api/oauth2/authorize?client_id=873204919593730119&permissions=8&scope=bot+applications.commands)\n────")
        invite_emb.set_thumbnail(url=ctx.me.display_avatar)
        invite_emb.set_author(
            name=f"{ctx.message.author} : Invite Links Below",
            icon_url=ctx.author.display_avatar.url)
        await ctx.reply(embed=invite_emb, mention_author=False)

    @commands.hybrid_command(
        name="usage",
        brief="Get command usage",
        aliases=["cu"])
    @commands.guild_only()
    async def usage(self, ctx: GeraltContext) -> Optional[discord.Message]:
        """Get a list of how many commands have been used here"""
        fetch_usage = await self.bot.db.fetch("SELECT * FROM meta WHERE guild_id = $1 ORDER BY uses DESC", ctx.guild.id)
        cmd_usage = [
            f"> │ ` - ` \"**{data['command_name']}**\" : `{data['uses']}` Times\n> │ ` - ` Last Used : {self.bot.timestamp(data['invoked_at'], style = 'R')}\n────\n" for data in fetch_usage]
        if not cmd_usage:
            return await ctx.reply(f"No one has invoked any command in \"**{ctx.guild}**\" still. Be the first one \N{HANDSHAKE}")

        embed_list = []
        while cmd_usage:
            cmd_usage_emb = BaseEmbed(
                title=f"Commands Used in {ctx.guild}",
                description="".join(cmd_usage[:5]),
                colour=self.bot.colour)
            cmd_usage_emb.set_footer(
                text="Shows from most used to least used commands")
            cmd_usage_emb.set_thumbnail(url=ctx.guild.icon.url)
            cmd_usage = cmd_usage[5:]
            embed_list.append(cmd_usage_emb)
        await Paginator(self.bot, ctx, embeds=embed_list).send(ctx)

    @commands.hybrid_command(
        name="source",
        brief="Returns Source",
        aliases=["src"])
    @app_commands.checks.cooldown(2, 5)
    @commands.cooldown(2, 5, commands.BucketType.user)
    @app_commands.describe(command="A command you want to get the source for.")
    async def source(self, ctx: GeraltContext, *, command: str = None) -> Optional[discord.Message]:
        """Returns source for a command"""
        view = discord.ui.View()
        branch = "stellar-v2"
        repo_url = "https://github.com/BSOD2528/Geralt"
        repository = await self.bot.git.get_repo("BSOD2528", "Geralt")
        line_count = await total_lines("source", ".py")

        source_emb = BaseEmbed(
            title=f"Github - {repository.full_name}",
            description=f"Take away the entire repo\n────\n<:Join:932976724235395072> {repository.description}",
            url=repository.html_url,
            colour=self.bot.colour)
        source_emb.add_field(
            name="Total Lines",
            value=f"<:Reply:930634822865547294> `{line_count + 10}`")
        source_emb.add_field(
            name="Stars",
            value=f"<:Reply:930634822865547294> `{repository.stargazers_count}`")
        source_emb.add_field(
            name="Language",
            value=f"<:Reply:930634822865547294> `{repository.language}`")
        source_emb.set_thumbnail(url=ctx.me.display_avatar.url)
        source_emb.set_footer(
            text=f"Invoked by {ctx.author}",
            icon_url=ctx.author.display_avatar.url)
        source_emb.set_author(
            name=f"\U00002728 Made with love by BSOD2528",
            icon_url=repository.owner.avatar_url,
            url=repository.owner.html_url)

        if command is None:
            view.add_item(
                discord.ui.Button(
                    label=f"Source for the entire repo!",
                    style=discord.ButtonStyle.link,
                    emoji="<a:Owner:905750348457738291>",
                    url=repository.html_url))
            view.add_item(
                discord.ui.Button(
                    label="Dashboard",
                    emoji="<:AkkoComfy:907104936368685106>",
                    url="https://bsod2528.github.io/Posts/Geralt"))
            return await ctx.reply(embed=source_emb, mention_author=False, view=view)

        obj = self.bot.get_command(command.replace(".", " "))

        if command == "help":
            src = type(self.bot.help_command)
            module = src.__module__
            file = inspect.getsourcefile(src)
        else:
            if obj is None:
                source_emb.description = f"Could not find command: `{command}`\n────\n<:Join:932976724235395072> {repository.description}"
                view.add_item(
                    discord.ui.Button(
                        label=f"Source for the entire repo!",
                        style=discord.ButtonStyle.link,
                        emoji="<a:Owner:905750348457738291>",
                        url=repository.html_url))
                view.add_item(
                    discord.ui.Button(
                        label="Dashboard",
                        emoji="<:AkkoComfy:907104936368685106>",
                        url="https://bsod2528.github.io/Posts/Geralt"))
                return await ctx.reply(embed=source_emb, mention_author=False, view=view)

            src = obj.callback.__code__
            module = obj.callback.__module__
            file = src.co_filename

        lines, line_beginning = inspect.getsourcelines(src)
        if not module.startswith("discord") or command == "help":
            path = os.path.relpath(file).replace("\\", "/")
        else:
            path = module.replace(".", "/") + ".py"

        url = f"{repo_url}/blob/{branch}/{path}#L{line_beginning}-L{line_beginning + len(lines) - 1}"

        source_emb.description = f"Here is the source for [`{command}`]({url})\n────\nEnsure to comply with [**GNU AGPL v3**](https://github.com/BSOD2528/Geralt/blob/stellar-v2/LICENSE) License"
        view.add_item(
            discord.ui.Button(
                label=f"Source for \"{command}\"",
                style=discord.ButtonStyle.link,
                emoji="<a:Owner:905750348457738291>",
                url=url))
        view.add_item(
            discord.ui.Button(
                label="Dashboard",
                emoji="<:AkkoComfy:907104936368685106>",
                url="https://bsod2528.github.io/Posts/Geralt"))
        await ctx.reply(embed=source_emb, mention_author=False, view=view)
