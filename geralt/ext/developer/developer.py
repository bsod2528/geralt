import asyncio
import contextlib
import io
import textwrap
import time
import traceback
from typing import Dict, Optional

import aiohttp
import discord
from discord.ext import commands

import geralt

from ...bot import CONFIG, BaseBot
from ...context import BaseContext
from ...embed import BaseEmbed
from ...kernel.utilities.crucial import Plural, TabulateData
from ...kernel.utilities.extensions import COGS_EXTENSIONS
from ...kernel.views.meta import Confirmation, Leave
from ...kernel.views.paginator import Paginator


class Developer(commands.Cog):
    """Developer Commands [ Bot owners only ]"""

    def __init__(self, bot: BaseBot):
        self.bot = bot

    @property
    def emote(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name="Dev", id=905750348457738291, animated=True)

    def cleanup_code(self, content: str):
        """Automatically removes code blocks from the code."""
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:-1])
        return content.strip("` \n")

    async def add_to_blacklist(
        self, ctx: BaseContext, snowflake: discord.Object, reason: str, url: str
    ):
        query = "INSERT INTO blacklist VALUES ($1, $2, $3, $4, $5)"
        if snowflake.id in self.bot.owner_ids:
            return await ctx.send(f"`{snowflake.id}` ─ is one of the owner's id.")

        if self.bot.get_channel(snowflake.id):
            try:
                await self.bot.db.execute(
                    query, snowflake.id, "channel", reason, discord.utils.utcnow(), url
                )
                return self.bot.blacklists.add(snowflake.id)
            except Exception as exception:
                return await ctx.send(f"```py\n{exception}\n```")

        if self.bot.get_user(snowflake.id):
            try:
                user = self.bot.get_user(snowflake.id)
                view = discord.ui.View()
                view.add_item(
                    discord.ui.Button(
                        label="Support",
                        style=discord.ButtonStyle.link,
                        url="https://discord.gg/JXEu2AcV5Y",
                        emoji="<a:BotLurk:905749164355379241>",
                    )
                )
                content = (
                    f"Dear **{user.mention}** <:SarahPray:920484222421045258> You have been blacklisted by **{ctx.author}**. Hence you are blocked from using my commands."
                    f" To appeal please contact **{ctx.author}** via my support server. The reason for which you have been blacklisted is given below :\n\n"
                    f">>> ─────\n{reason}\n─────"
                )
                try:
                    await user.send(content=content, view=view)
                except Exception:
                    return
                await self.bot.db.execute(
                    query, snowflake.id, "user", reason, discord.utils.utcnow(), url
                )
                return self.bot.blacklists.add(snowflake.id)
            except Exception as exception:
                return await ctx.send(f"```py\n{exception}\n```")

        if self.bot.get_guild(snowflake.id):
            try:
                await self.bot.db.execute(
                    query, snowflake.id, "guild", reason, discord.utils.utcnow(), url
                )
                return self.bot.blacklists.add(snowflake.id)
            except Exception as exception:
                return await ctx.send(f"```py\n{exception}\n```")

    async def remove_from_blacklist(self, ctx: BaseContext, snowflake: discord.Object):
        query = "DELETE FROM blacklist WHERE snowflake = $1"

        if self.bot.get_user(snowflake.id):
            user = self.bot.get_user(snowflake.id)
            view = discord.ui.View()
            view.add_item(
                discord.ui.Button(
                    label="Support",
                    style=discord.ButtonStyle.link,
                    url="https://discord.gg/JXEu2AcV5Y",
                    emoji="<a:BotLurk:905749164355379241>",
                )
            )
            content = f"Dear **{user.mention}** <:SarahPray:920484222421045258> You have been removed from blacklist by **{ctx.author}**. Hence you are now eligible to run my commands."
            try:
                await user.send(content=content, view=view)
            except Exception:
                return
            await self.bot.db.execute(query, snowflake.id)
            return self.bot.blacklists.remove(snowflake)

        try:
            await self.bot.db.execute(query, snowflake.id)
            return self.bot.blacklists.remove(snowflake)
        except Exception as exception:
            await ctx.reply(f"```py\n{exception}\n```")
            await ctx.add_nanocross()

    # Shuts the bot down in a friendly manner.
    @commands.command(name="die", brief="Eternal Sleep", aliases=["snap", "sleep"])
    @commands.is_owner()
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def die(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Sends the bot to eternal sleep"""

        async def yes(
            ui: discord.ui.View,
            interaction: discord.Interaction,
            button: discord.ui.button,
        ):
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            await ui.response.edit(
                content="Let me die in peace",
                view=ui,
                allowed_mentions=self.bot.mentions,
            )
            await self.bot.change_presence(
                status=discord.Status.do_not_disturb,
                activity=discord.Activity(
                    type=discord.ActivityType.playing, name=f"Let me Die in Peace"
                ),
            )
            await asyncio.sleep(5)
            await ui.response.edit(
                content="Dead!", view=ui, allowed_mentions=self.bot.mentions
            )
            async with aiohttp.ClientSession() as session:
                death_webhook = discord.Webhook.partial(
                    id=CONFIG.get("NOTIF_ID"),
                    token=CONFIG.get("NOTIF_TOKEN"),
                    session=session,
                )
                await death_webhook.send(
                    content=f"<:GeraltRightArrow:904740634982760459> Going to die right at {self.bot.timestamp(discord.utils.utcnow(), style = 'F')} Byee <a:Byee:915568796536815616>\n───\n|| Break Point ||"
                )
                await session.close()
            await self.bot.close()

        async def no(
            ui: discord.ui.View,
            interaction: discord.Interaction,
            button: discord.ui.button,
        ):
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            await ui.response.edit(
                content="Seems like I'm gonna be alive for a bit longer",
                view=ui,
                allowed_mentions=self.bot.mentions,
            )

        async with ctx.channel.typing():
            await asyncio.sleep(0.1)
            Confirmation.response = await ctx.reply(
                "Do you want to kill me?",
                view=Confirmation(ctx, yes, no),
                allowed_mentions=self.bot.mentions,
            )

    @commands.command(name="dm", brief="dm them")
    @commands.is_owner()
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def dm(
        self, ctx: BaseContext, user: discord.User, *, message: str
    ) -> Optional[discord.Message]:
        """DM a particular user."""
        try:
            view = discord.ui.View()
            view.add_item(
                discord.ui.Button(
                    label="Support",
                    style=discord.ButtonStyle.link,
                    url="https://discord.gg/JXEu2AcV5Y",
                    emoji="<a:BotLurk:905749164355379241>",
                )
            )
            await user.send(
                f"<:GeraltRightArrow:904740634982760459> You have received a DM from **{ctx.author}**. If you have any queries, join our support server :\n\n>>> ─────\n{message}\n─────",
                view=view,
            )
            await ctx.add_nanotick()
        except Exception as exception:
            await ctx.send(exception)

    # Evaluate command for running both asynchronous and sychronous programs.
    @commands.command(name="eval", brief="Run Code", aliases=["e"])
    @commands.is_owner()
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def eval(self, ctx: BaseContext, *, body: str) -> Optional[discord.Message]:
        """Running both asynchronous and sychronous programs"""
        environment: Dict[str, object] = {
            "ctx": ctx,
            "bot": self.bot,
            "self": self,
            "discord": discord,
            "message": ctx.message,
            "author": ctx.author,
            "guild": ctx.guild,
            "channel": ctx.channel,
            "embed": BaseEmbed,
            "file": discord.File,
            "geralt": geralt,
        }

        environment.update(globals())
        if body.startswith("```") and body.endswith("```"):
            body = "\n".join(body.split("\n")[1:-1])
        body = body.strip("` \n")
        stdout = io.StringIO()
        compile = f"async def func():\n{textwrap.indent(body, '  ')}"
        try:
            exec(compile, environment)
        except Exception as exception:
            return await ctx.send(
                f"```py\n{exception.__class__.__name__} : {exception}\n```"
            )
        func = environment["func"]
        try:
            with contextlib.redirect_stdout(stdout):
                returned_value = await func()
        except Exception as exception:
            value = stdout.getvalue()
            message = await ctx.send(f"```py\n{value} {traceback.format_exc()}\n```")
            await ctx.message.add_reaction("<:WinUnheck:898572376147623956>")
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction("<:WinCheck:898572324490604605>")
            except BaseException:
                pass
            if returned_value is None:
                if value:
                    await ctx.send(f"```py\n{value}\n```", mention_author=False)
            else:
                await ctx.send(
                    f"```py\n{value}{returned_value}\n```", mention_author=False
                )

    # Loads extension of choice
    @commands.command(name="load", brief="Loads Cog", aliases=["l"])
    @commands.is_owner()
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def load(self, ctx: BaseContext, *, cog: str) -> Optional[discord.Message]:
        """Loads the Extension mentioned."""
        try:
            await self.bot.load_extension(f"geralt.ext.{cog}")
            async with ctx.channel.typing():
                await asyncio.sleep(0.1)
            await ctx.reply(
                f'"**{cog}**" : Successfully Loaded <:RavenPray:914410353155244073>',
                allowed_mentions=self.bot.mentions,
            )
        except Exception as exception:
            async with ctx.channel.typing():
                await asyncio.sleep(0.1)
            await ctx.reply(
                f'Couldn\'t load "**{cog}**" :\n```py\n{exception}\n```',
                allowed_mentions=self.bot.mentions,
            )

    # Unloads extension of choice
    @commands.command(name="unload", brief="Unloads Cog", aliases=["ul"])
    @commands.is_owner()
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def unload(self, ctx: BaseContext, *, cog: str) -> Optional[discord.Message]:
        """Unloads the Extension mentioned."""
        try:
            await self.bot.unload_extension(f"geralt.ext.{cog}")
            async with ctx.channel.typing():
                await asyncio.sleep(0.1)
            await ctx.reply(
                f'"**{cog}**" : Successfully Unloaded <:RavenPray:914410353155244073>',
                allowed_mentions=self.bot.mentions,
            )
        except Exception as exception:
            async with ctx.channel.typing():
                await asyncio.sleep(0.1)
            await ctx.reply(
                f'Couldn\'t unload "**{cog}**" :\n```py\n{exception}\n```',
                allowed_mentions=self.bot.mentions,
            )

    # Reloads extension of choice
    @commands.command(name="reload", brief="Reloads Cog", aliases=["rl"])
    @commands.is_owner()
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def reload(
        self, ctx: BaseContext, *, cog: str = None
    ) -> Optional[discord.Message]:
        """Reloads the Extension mentioned."""
        if cog is None:
            try:
                for cogs in COGS_EXTENSIONS:
                    await self.bot.reload_extension(cogs)
                await ctx.reply(
                    f"Reloaded `{len(cogs)}` files <:RavenPray:914410353155244073>",
                    allowed_mentions=self.bot.mentions,
                )
            except Exception as exception:
                async with ctx.channel.typing():
                    await asyncio.sleep(0.1)
                    await ctx.reply(
                        f"Couldn't reload all the extensions : \n```py\n{exception}\n```",
                        allowed_mentions=self.bot.mentions,
                    )
        else:
            try:
                await self.bot.reload_extension(f"geralt.ext.{cog}")
                async with ctx.channel.typing():
                    await asyncio.sleep(0.1)
                await ctx.reply(
                    f'"**{cog}**" : Successfully Reloaded <:RavenPray:914410353155244073>',
                    allowed_mentions=self.bot.mentions,
                )
            except Exception as exception:
                async with ctx.channel.typing():
                    await asyncio.sleep(0.1)
                    await ctx.reply(
                        f'Couldn\'t reload "**{cog}**" : \n```py\n{exception}\n```',
                        allowed_mentions=self.bot.mentions,
                    )

    # Group of Commands used for changing presence.
    @commands.group(name="dev", brief="Simple Dev Stuff", aliases=["devmode"])
    @commands.is_owner()
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def dev(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Simple commands for dev to do"""
        if ctx.invoked_subcommand is None:
            return await ctx.command_help()

    @dev.command(name="no-prefix", brief="Set Prefix to Nill", aliases=["np"])
    async def no_prefix(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Sets the prefix to ` `."""
        if self.bot.no_prefix is False:
            self.bot.no_prefix = True
            return await ctx.add_nanotick()
        self.bot.no_prefix = False
        await ctx.add_nanocross()

    @dev.command(name="total-guilds", aliases=["tg"], brief="Sends Guild List")
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def total_guilds(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Sends the entire guild list."""
        await ctx.reply(
            f"Currently in `{len(self.bot.guilds)}` Guilds.",
            allowed_mentions=self.bot.mentions,
        )
        await ctx.send(
            f" ".join(
                [
                    f'> │ ` ─ ` "{g.name}" : {g.owner.mention} (`{g.id}`)\n'
                    for g in self.bot.guilds
                ]
            )
            + "",
            allowed_mentions=self.bot.mentions,
        )

    @dev.command(name="on", brief="Sets Developer Mode On")
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def on(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Sets Developer Mode On"""
        self.bot.developer_mode = True
        await self.bot.change_presence(status=discord.Status.invisible)
        await ctx.message.add_reaction("<:Offline:905757032521551892>")

    @dev.command(name="off", brief="Sets Developer Mode Off")
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def off(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Sets Developer Mode Off"""
        self.bot.developer_mode = False
        await self.bot.change_presence(
            status=discord.Status.idle,
            activity=discord.Activity(
                type=discord.ActivityType.listening, name=".ghelp"
            ),
        )
        await ctx.message.add_reaction("<:Idle:905757063064453130>")

    @dev.command(name="alltags", brief="Sends all tags", aliases=["at"])
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def all_tags(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Sends tags from all guilds"""
        tag_fetch = await self.bot.db.fetch("SELECT * FROM tags ORDER BY id")
        tag_list = []
        serial_no = 1
        for tags in tag_fetch:
            tag_list.append(
                f"> [**{serial_no})**]({tags['jump_url']}) \"**{tags['name']}**\"\n> │ ` ─ ` Owner : \"**{tags['author_name']}**\" (`{tags['author_id']}`)\n> │ ` ─ ` ID : `{tags['id']}` │ Uses : `{tags['uses']}`\n> │ ` ─ ` Created : {self.bot.timestamp(tags['created_on'], style = 'R')}\n────\n"
            )
            serial_no += 1
        embed_list = []
        while tag_list:
            tag_list_emb = BaseEmbed(
                title=f"Global Tag List :",
                description="".join(tag_list[:5]),
                colour=self.bot.colour,
            )
            tag_list_emb.set_footer(
                text=f"Run {ctx.clean_prefix}tag for more sub ─ commands."
            )
            tag_list = tag_list[5:]
            embed_list.append(tag_list_emb)
        await Paginator(self.bot, ctx, embeds=embed_list).send(ctx)

    @commands.command(name="guildfetch", brief="Get guild information", aliases=["fg"])
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.is_owner()
    async def guild_fetch(
        self, ctx: BaseContext, *, guild: discord.Guild
    ) -> Optional[discord.Message]:
        """Get entire details about the guild."""
        fetched_guild = await self.bot.fetch_guild(guild.id)
        fetched_guild_emb = BaseEmbed(
            title=f":scroll: {guild.name}'s Information", colour=self.bot.colour
        )
        fetched_guild_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> General Information :",
            value=f"> **Owner :** {guild.owner} (`{guild.owner.id}`) \n"
            f"> **Identification No. :** `{guild.id}` \n"
            f"> **Made On :** {self.bot.timestamp(guild.created_at)} \n"
            f"> **Joined On :** {self.bot.timestamp(guild.me.joined_at)}",
        )
        fetched_guild_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Channel Information :",
            value=f"> **Text :** `{len(guild.text_channels)}` \n"
            f"> **Voice :** `{len(guild.voice_channels)}` \n"
            f"> **Threads :** `{len(guild.threads)}` \n"
            f"> **Stage :** `{len(guild.stage_channels)}` \n",
            inline=False,
        )
        fetched_guild_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> No. of User :",
            value=f"> **No. of Humans :** `{len(list(filter(lambda U : U.bot is False, guild.members)))}` \n"
            f"> **No. of Bots :** `{len(list(filter(lambda U : U.bot, guild.members)))}` \n"
            f"> **Total :** `{guild.member_count}` \n",
            inline=False,
        )
        try:
            fetched_guild_emb.set_thumbnail(url=guild.icon.url)
        except AttributeError:
            pass

        leave_view = Leave(ctx, guild)
        if fetched_guild.banner is None:
            async with ctx.channel.typing():
                await asyncio.sleep(0.1)
            leave_view.message = await ctx.reply(
                embed=fetched_guild_emb, mention_author=False, view=leave_view
            )
        else:
            fetched_guild_emb.set_image(url=fetched_guild.banner.url)
            async with ctx.channel.typing():
                await asyncio.sleep(0.1)
            leave_view.message = await ctx.reply(
                embed=fetched_guild_emb, mention_author=False, view=leave_view
            )

    # Taken from R.Danny Bot by Rapptz - Danny [ Github Profile Name ]
    @commands.command(name="sql", brief="Query DB")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.is_owner()
    async def sql(self, ctx: BaseContext, *, query: str) -> Optional[discord.Message]:
        """Run SQL Queries"""
        query = self.cleanup_code(query)

        multi_line = query.count(";") > 1
        if multi_line:
            method = self.bot.db.execute
        else:
            method = self.bot.db.fetch
        try:
            db_start = time.perf_counter()
            results = await method(query)
            latency = (time.perf_counter() - db_start) * 1000.0
        except Exception:
            return await ctx.reply(
                f"```py\n{traceback.format_exc()}\n```", mention_author=False
            )

        rows = len(results)
        if multi_line or rows == 0:
            return await ctx.send(
                f"<:GeraltRightArrow:904740634982760459> No records were for found for the following query : ```sql\n{query}\n```"
            )

        headers = list(results[0].keys())
        table = TabulateData()
        table.columns(headers)
        table.rows_added(list(r.values()) for r in results)
        rendered = table.render()

        final = f"{rendered}\n"
        async with ctx.channel.typing():
            await asyncio.sleep(0.1)
        await ctx.reply(
            f"<:GeraltRightArrow:904740634982760459> Returned {Plural(rows):row} in {latency:.2f}ms",
            file=discord.File(io.StringIO(final), filename="Query-Result.sql"),
            allowed_mentions=self.bot.mentions,
        )

    @commands.group(name="blacklist", brief="Blacklist Objects", aliases=["bl"])
    @commands.is_owner()
    async def blacklist(self, ctx: BaseContext):
        """Group of commands to block objects from using me."""
        if ctx.invoked_subcommand is None:
            await ctx.command_help()

    @blacklist.command(name="add", brief="Add objects to the list")
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def blacklist_add(
        self, ctx: BaseContext, snowflake: discord.Object, *, reason: str = None
    ) -> Optional[discord.Message]:
        """Add objects to blacklist."""
        reason = reason or "Not Specified"
        try:
            await self.add_to_blacklist(ctx, snowflake, reason, ctx.message.jump_url)
            await ctx.add_nanotick()
        except KeyError:
            await ctx.reply(f"**{snowflake}** has already been blacklisted.")
            await ctx.add_nanocross()

    @blacklist.command(name="remove", brief="Remove them from the list")
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def blacklist_remove(
        self, ctx: BaseContext, snowflake: discord.Object
    ) -> Optional[discord.Message]:
        """Remove objects from blacklist."""
        await self.remove_from_blacklist(ctx, snowflake)

    @blacklist.command(name="all", brief="Sends all blacklisted objects.")
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def blacklisted_all(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Get a list of blacklisted objects."""
        query = "SELECT snowflake, object, reason, queried_at, jump_url FROM blacklist"
        fetched_blacklisted_objects = await self.bot.db.fetch(query)
        blacklisted_objects = []
        serial_no = 1
        for data in fetched_blacklisted_objects:
            blacklisted_objects.append(
                f"> [**{serial_no}).**]({data[4]}) ─ **{data[1]}** (`{data[0]}`)\n> │ ` ─ ` Reason : \"{data[2]}\"\n> │ ` ─ ` Blacklisted : {self.bot.timestamp(data[3], style = 'R')}\n────\n"
            )
            serial_no += 1

        if not fetched_blacklisted_objects:
            await ctx.reply("Seems like you haven't blacklisted any object \U0001f440")
        else:
            if serial_no <= 2:
                blacklisted_emb = BaseEmbed(
                    title=f"\U0001f4dc Blacklisted Objects",
                    description=f"".join(blacklisted_objects),
                    colour=self.bot.colour,
                )
                await ctx.reply(embed=blacklisted_emb, mention_author=False)
            else:
                embed_list = []
                while blacklisted_objects:
                    blacklisted_emb = BaseEmbed(
                        title=f"\U0001f4dc Blacklisted Objects",
                        description=f"".join(blacklisted_objects[:2]),
                        colour=self.bot.colour,
                    )
                    blacklisted_objects = blacklisted_objects[2:]
                    embed_list.append(blacklisted_emb)
                await Paginator(self.bot, ctx, embeds=embed_list).send(ctx)

    @commands.command(name="self-purge")
    @commands.is_owner()
    async def de(
        self, ctx: BaseContext, limit: int = None
    ) -> Optional[discord.Message]:
        """Delete a referenced message or purge few."""
        if (
            ctx.message.reference
            and ctx.message.reference.resolved.author == self.bot.user
        ):
            await ctx.message.reference.resolved.delete()
            try:
                await ctx.message.delete()
                await ctx.add_nanotick()
            except Exception as exception:
                await ctx.send(f"```py\\{exception}\n```")
                await ctx.add_nanocross()
        if not limit:
            limit = 10
        await ctx.channel.purge(
            limit=limit, check=lambda u: u.author == self.bot.user, bulk=False
        )
        try:
            await ctx.message.delete()
            await ctx.add_nanotick()
        except Exception as exception:
            await ctx.send(f"```py\n{exception}\n```")
            await ctx.add_nanocross()

    @commands.command(name="keepalive", brief="Keeps the guild alive", aliases=["ka"])
    @commands.is_owner()
    async def keep_alive(self, ctx: BaseContext):
        """Keeps the Among 3 guild alive"""
        if ctx.guild.id != 913809986386284544:
            return await ctx.reply(f"**{ctx.author}** - this is not among three guild.")
        for _ in range(20):
            await asyncio.sleep(30)
            await ctx.send("br")
