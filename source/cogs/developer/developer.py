import io
import time
import typing
import aiohttp
import asyncio
import discord
import textwrap
import traceback
import contextlib

from types import NoneType
from discord.ext import commands

from ...kernel.views.paginator import Paginator
from ...kernel.subclasses.embed import BaseEmbed
from ...kernel.views.meta import Leave, Confirmation
from ...kernel.subclasses.context import GeraltContext
from ...kernel.utilities.crucial import Plural, TabulateData
from ...kernel.subclasses.bot import CONFIG, COGS_EXTENSIONS, Geralt

class SyncFlag(commands.FlagConverter, prefix = "--", delimiter = " ", case_insensitive = True):
    cosmic: str = NoneType

class Developer(commands.Cog):
    """Developer Commands [ Bot owners only ]"""
    def __init__(self, bot: Geralt):
        self.bot = bot
    
    @property
    def emote(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name = "Dev", id = 905750348457738291, animated = True)   
    
    def cleanup_code(self, content: str):
        """Automatically removes code blocks from the code."""
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:-1])
        return content.strip("` \n")

    @commands.command(
        name = "no-prefix",
        brief = "Sets prefix to \" \"",
        aliases = ["np"])
    @commands.is_owner()
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def no_prefix(self, ctx: GeraltContext):
        if self.bot.no_prefix is False:
            self.bot.no_prefix = True
            return await ctx.add_nanotick()
        self.bot.no_prefix = False
        await ctx.add_nanocross()

    # Shuts the bot down in a friendly manner.
    @commands.command(
        name = "die",
        brief = "Eternal Sleep",
        aliases = ["snap", "sleep"])
    @commands.is_owner()
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def die(self, ctx: GeraltContext) -> typing.Optional[discord.Message]:
        """Sends the bot to eternal sleep"""
        async def yes(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.button):
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            await ui.response.edit(content = "Let me die in peace", view = ui, allowed_mentions = self.bot.mentions)
            await self.bot.change_presence(
                status = discord.Status.do_not_disturb,
                activity = discord.Activity(type = discord.ActivityType.playing, name = f"Let me Die in Peace")) 
            await asyncio.sleep(5)
            await ui.response.edit(content = "Dead!", view = ui, allowed_mentions = self.bot.mentions)
            async with aiohttp.ClientSession() as session:
                death_webhook = discord.Webhook.partial(id = CONFIG.get("NOTIF_ID"), token = CONFIG.get("NOTIF_TOKEN"), session = session)
                await death_webhook.send(content = f"<:GeraltRightArrow:904740634982760459> Going to die right at {self.bot.timestamp(discord.utils.utcnow(), style = 'F')} Byee <a:Byee:915568796536815616>\n───\n|| Break Point ||")
                await session.close()
            await self.bot.close()

        async def no(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.button):
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            await ui.response.edit(content = "Seems like I'm gonna be alive for a bit longer", view = ui, allowed_mentions = self.bot.mentions)
        async with ctx.channel.typing():
            await asyncio.sleep(0.1)
            Confirmation.response = await ctx.reply("Do you want to kill me?", view = Confirmation(ctx, yes, no), allowed_mentions = self.bot.mentions)

    @commands.command(
        name = "dm", 
        brief = "dm them")
    @commands.is_owner()
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def dm(self, ctx: GeraltContext, user: discord.User, *, message: str) -> typing.Optional[discord.Message]:
        """DM a particular user."""
        try:
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label = "Support", style = discord.ButtonStyle.link, url = "https://discord.gg/JXEu2AcV5Y", emoji = "<a:BotLurk:905749164355379241>"))
            await user.send(f"<:GeraltRightArrow:904740634982760459> You have received a DM from **{ctx.author}**. If you have any queries, join our support server :\n\n>>> ─────\n{message}\n─────", view = view)
            await ctx.add_nanotick()
        except Exception as exception:
            await ctx.send(exception)

    # Evaluate command for running both asynchronous and sychronous programs.
    @commands.command(
        name = "eval",
        brief = "Run Code",
        aliases = ["e"])
    @commands.is_owner()
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def eval(self, ctx: GeraltContext, *, body: str) -> typing.Optional[discord.Message]:
        """Running both asynchronous and sychronous programs"""
        environment = {
            "ctx" : ctx,
            "bot" : self.bot,
            "self" : self,
            "discord" : discord,
            "message" : ctx.message,
            "author" : ctx.author,
            "guild" : ctx.guild,
            "channel" : ctx.channel,
        }

        environment.update(globals())
        if body.startswith( "```" ) and body.endswith( "```" ):
            body = "\n".join(body.split("\n")[1:-1])
        body = body.strip("` \n")
        stdout = io.StringIO()
        compile = f"async def func():\n{textwrap.indent(body, '  ')}"
        try:    
            exec(compile, environment)
        except Exception as exception:
            return await ctx.send(f"```py\n{exception.__class__.__name__} : {exception}\n```")
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
            except:
                pass
            if returned_value is None:
                if value:
                    await ctx.send(f"```py\n{value}\n```", mention_author = False)
            else:
                await ctx.send(f"```py\n{value}{returned_value}\n```", mention_author = False)

    # Loads extension of choice
    @commands.command(
        name = "load",
        brief = "Loads Cog",
        aliases = ["l"])
    @commands.is_owner()
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def load(self, ctx: GeraltContext, *, cog: str) -> typing.Optional[discord.Message]:
        """Loads the Extension mentioned."""
        try:
            await self.bot.load_extension(f"source.cogs.{cog}")
            async with ctx.channel.typing():
                await asyncio.sleep(0.1)
            await ctx.reply(f"\"**{cog}**\" : Successfully Loaded <:RavenPray:914410353155244073>", allowed_mentions = self.bot.mentions)
        except Exception as exception:
            async with ctx.channel.typing():
                await asyncio.sleep(0.1)
            await ctx.reply(f"Couldn't load \"**{cog}**\" :\n```py\n{exception}\n```", allowed_mentions = self.bot.mentions)

    # Unloads extension of choice
    @commands.command(
        name = "unload",
        brief = "Unloads Cog",
        aliases = ["ul"])
    @commands.is_owner()
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def unload(self, ctx: GeraltContext, *, cog: str) -> typing.Optional[discord.Message]:
        """Unloads the Extension mentioned."""
        try:
            await self.bot.unload_extension(f"source.cogs.{cog}")
            async with ctx.channel.typing():
                await asyncio.sleep(0.1)
            await ctx.reply(f"\"**{cog}**\" : Successfully Unloaded <:RavenPray:914410353155244073>", allowed_mentions = self.bot.mentions)
        except Exception as exception:
            async with ctx.channel.typing():
                await asyncio.sleep(0.1)
            await ctx.reply(f"Couldn't unload \"**{cog}**\" :\n```py\n{exception}\n```", allowed_mentions = self.bot.mentions)
 
    # Reloads extension of choice
    @commands.command(
        name = "reload",
        brief = "Reloads Cog",
        aliases = ["rl"])
    @commands.is_owner()
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def reload(self, ctx: GeraltContext, *, cog: str = None) -> typing.Optional[discord.Message]:
        """Reloads the Extension mentioned."""
        if cog is None:
            try:
                for cogs in COGS_EXTENSIONS:
                    await self.bot.reload_extension(cogs)
                await ctx.reply(f"Reloaded `{len(cogs)}` files <:RavenPray:914410353155244073>")
            except Exception as exception:
                async with ctx.channel.typing():
                    await asyncio.sleep(0.1)
                    await ctx.reply(f"Couldn't reload all the extensions : \n```py\n{exception}\n```", allowed_mentions = self.bot.mentions)
        else:
            try:
                await self.bot.reload_extension(f"source.cogs.{cog}")
                async with ctx.channel.typing():
                    await asyncio.sleep(0.1)
                await ctx.reply(f"\"**{cog}**\" : Successfully Reloaded <:RavenPray:914410353155244073>", allowed_mentions = self.bot.mentions)
            except Exception as exception:
                async with ctx.channel.typing():
                    await asyncio.sleep(0.1)
                    await ctx.reply(f"Couldn't reload \"**{cog}**\" : \n```py\n{exception}\n```", allowed_mentions = self.bot.mentions)
  
    # Group of Commands used for changing presence.
    @commands.group(
        name = "dev",
        brief = "Simple Dev Stuff",
        aliases = ["devmode"])
    @commands.is_owner()
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def dev(self, ctx: GeraltContext) -> typing.Optional[discord.Message]:
        """Simple commands for dev to do"""
        if ctx.invoked_subcommand is None:
            await ctx.command_help()

    @dev.command(
        name  = "total-guilds",
        aliases = ["tg"],
        brief = "Sends Guild List")
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def total_guilds(self, ctx: GeraltContext) -> typing.Optional[discord.Message]:
        """Sends the entire guild list."""
        await ctx.reply(f"Currently in `{len(self.bot.guilds)}` Guilds.", allowed_mentions = self.bot.mentions)
        await ctx.send(f" ".join([f"> │ ` ─ ` \"{g.name}\" : {g.owner.mention} (`{g.id}`)\n" for g in self.bot.guilds]) + "", allowed_mentions = self.bot.mentions)
  
    @dev.command(
        name = "on",
        brief = "Sets Developer Mode On")
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def on(self, ctx: GeraltContext) -> typing.Optional[discord.Message]:
        """Sets Developer Mode On"""
        self.bot.developer_mode = True
        await self.bot.change_presence(
            status = discord.Status.invisible)
        await ctx.message.add_reaction("<:Offline:905757032521551892>")

    @dev.command(
        name = "off",
        brief = "Sets Developer Mode Off")
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def off(self, ctx: GeraltContext) -> typing.Optional[discord.Message]:
        """Sets Developer Mode Off"""
        self.bot.developer_mode = False
        await self.bot.change_presence(
            status = discord.Status.idle,
            activity = discord.Activity(type = discord.ActivityType.listening, name = ".ghelp"))
        await ctx.message.add_reaction("<:Idle:905757063064453130>")
    
    @dev.command(
        name = "alltags",
        brief = "Sends all tags",
        aliases = ["at"])
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def all_tags(self, ctx: GeraltContext) -> typing.Optional[discord.Message]:
        """Sends tags from all guilds"""
        tag_fetch = await self.bot.db.fetch("SELECT * FROM tags ORDER BY id")
        tag_list = []
        serial_no = 1
        for tags in tag_fetch:
            tag_list.append(f"> [**{serial_no})**]({tags['jump_url']}) \"**{tags['name']}**\"\n> │ ` ─ ` Owner : \"**{tags['author_name']}**\" (`{tags['author_id']}`)\n> │ ` ─ ` ID : `{tags['id']}` │ Uses : `{tags['uses']}`\n> │ ` ─ ` Created : {self.bot.timestamp(tags['created_on'], style = 'R')}\n────\n")
            serial_no += 1
        embed_list = []
        while tag_list:
            tag_list_emb = BaseEmbed(
                title = f"Global Tag List :",
                description = "".join(tag_list[:5]),
                colour = self.bot.colour)
            tag_list_emb.set_footer(text = f"Run {ctx.clean_prefix}tag for more sub ─ commands.")
            tag_list = tag_list[5:]
            embed_list.append(tag_list_emb)     
        await Paginator(self.bot, ctx, embeds = embed_list).send(ctx) 

    @commands.command(
        name = "guildfetch",
        brief = "Get guild information",
        aliases = ["fg"])
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.is_owner()
    async def guild_fetch(self, ctx: GeraltContext, *, guild: discord.Guild) -> typing.Optional[discord.Message]:
        """Get entire details about the guild."""        
        fetched_guild = await self.bot.fetch_guild(guild.id)
        fetched_guild_emb = BaseEmbed(
            title = f":scroll: {guild.name}'s Information",
            colour = self.bot.colour)
        fetched_guild_emb.add_field(
            name = "<:GeraltRightArrow:904740634982760459> General Information :",
            value = f"> **Owner :** {guild.owner} (`{guild.owner.id}`) \n" \
                    f"> **Identification No. :** `{guild.id}` \n" \
                    f"> **Made On :** {self.bot.timestamp(guild.created_at)} \n" \
                    f"> **Joined On :** {self.bot.timestamp(guild.me.joined_at)}")
        fetched_guild_emb.add_field(
            name = "<:GeraltRightArrow:904740634982760459> Channel Information :",
            value = f"> **Text :** `{len(guild.text_channels)}` \n" \
                    f"> **Voice :** `{len(guild.voice_channels)}` \n" \
                    f"> **Threads :** `{len(guild.threads)}` \n" \
                    f"> **Stage :** `{len(guild.stage_channels)}` \n",
            inline = False)
        fetched_guild_emb.add_field(
            name = "<:GeraltRightArrow:904740634982760459> No. of User :",
            value = f"> **No. of Humans :** `{len(list(filter(lambda U : U.bot is False, guild.members)))}` \n" \
                    f"> **No. of Bots :** `{len(list(filter(lambda U : U.bot, guild.members)))}` \n" \
                    f"> **Total :** `{guild.member_count}` \n",
            inline = False)
        fetched_guild_emb.set_thumbnail(url = guild.icon.url)

        if fetched_guild.banner is None:
            async with ctx.channel.typing():
                await asyncio.sleep(0.1)
            await ctx.reply(embed = fetched_guild_emb, mention_author = False, view = Leave(ctx, guild))
        else:
            fetched_guild_emb.set_image(url = fetched_guild.banner.url)
            async with ctx.channel.typing():
                await asyncio.sleep(0.1)
            await ctx.reply(embed = fetched_guild_emb, mention_author = False, view = Leave(ctx, guild))
        
    # Taken from R.Danny Bot by Rapptz - Danny [ Github Profile Name ]
    @commands.command(
        name = "sql",
        brief = "Query DB")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.is_owner()
    async def sql(self, ctx: GeraltContext, *, query: str) -> typing.Optional[discord.Message]:
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
            return await ctx.reply(f"```py\n{traceback.format_exc()}\n```", mention_author = False)

        rows = len(results)
        if multi_line or rows == 0:
            return await ctx.send(f"<:GeraltRightArrow:904740634982760459> No records were for found for the following query : ```sql\n{query}\n```")

        headers = list(results[0].keys())
        table = TabulateData()
        table.columns(headers)
        table.rows_added(list(r.values()) for r in results)
        rendered = table.render()

        final = f"{rendered}\n"
        async with ctx.channel.typing():
            await asyncio.sleep(0.1)
        await ctx.reply(f"<:GeraltRightArrow:904740634982760459> Returned {Plural(rows):row} in {latency:.2f}ms", file = discord.File(io.StringIO(final), filename = "Query-Result.sql"), allowed_mentions = self.bot.mentions)
      
    @commands.command(
        name = "sync",
        brief = "Sync App Commands")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @commands.is_owner()
    async def cmd_sync(self, ctx: GeraltContext, *, flag: typing.Optional[SyncFlag]) -> typing.Optional[discord.Message]:
        """Syncs application commands.
        ────
        **Flags Present :**
        `--cosmos` : When passed syncs globally
        **Example :**
        `.gsync [--cosmos]`"""
        if not flag:
            try:
                await self.bot.tree.sync(guild = discord.Object(id = 889522892088410142))
                await ctx.message.add_reaction("<:DuckThumbsUp:917007413259956254>")
            except Exception:
                message = await ctx.reply(f"```py\n{Exception}\n```")
                await message.add_reaction("<a:LifeSucks:932255208044650596>")
        if flag:
            try:
                await self.bot.tree.sync()
                await ctx.message.add_reaction("<:DuckThumbsUp:917007413259956254>")
            except Exception:
                message = await ctx.reply(f"```py\n{Exception}\n```")
                await message.add_reaction("<a:LifeSucks:932255208044650596>")

    @commands.group(
        name = "blacklist",
        brief = "Blacklist People",
        aliases = ["bl"])
    @commands.is_owner()
    async def blacklist(self, ctx: GeraltContext):
        """Group of commands to block people from using me."""
        if ctx.invoked_subcommand is None:
            await ctx.command_help()
    
    @blacklist.command(
        name = "add",
        brief = "Add them to the list")
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def blacklist_add(self, ctx: GeraltContext, user: typing.Union[discord.User, discord.Member], *, reason: str = None) -> typing.Optional[discord.Message]:
        """Add users to blacklist."""
        reason = reason or "Not Specified"
        try:
            await self.bot.add_to_blacklist(user, reason, ctx.message.jump_url)
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label = "Support", style = discord.ButtonStyle.link, url = "https://discord.gg/JXEu2AcV5Y", emoji = "<a:BotLurk:905749164355379241>"))
            content = f"Dear **{user.mention}** <:SarahPray:920484222421045258> You have been blacklisted by **{ctx.author}**. Hence you are blocked from using my commands." \
                      f" To appeal please contact **{ctx.author}** via my support server. The reason for which you have been blacklisted is given below :\n\n" \
                      f">>> ─────\n{reason}\n─────"
            try:
                await user.send(content = content, view = view)
            except Exception:
                return
            await ctx.add_nanotick()
        except KeyError:
            await ctx.reply(f"**{user}** has already been blacklisted.")
            await ctx.add_nanocross()
        except Exception:
            await ctx.send(Exception)

    @blacklist.command(
        name = "remove",
        brief = "Remove them from the list")
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def blacklist_remove(self, ctx: GeraltContext, user: typing.Union[discord.User, discord.Member]) -> typing.Optional[discord.Message]:
        """Remove users from blacklist."""
        try:
            await self.bot.remove_from_blacklist(user)
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label = "Support", style = discord.ButtonStyle.link, url = "https://discord.gg/JXEu2AcV5Y", emoji = "<a:BotLurk:905749164355379241>"))
            content = f"Dear **{user.mention}** <:SarahPray:920484222421045258> You have been removed from blacklisting by **{ctx.author}**. You are now eligible to run all of my commands."         
            try:
                await user.send(content = content, view = view)
            except Exception:
                return
            await ctx.add_nanotick()
        except KeyError:
            await ctx.reply(f"**{user}** has already been whitelisted.")
            await ctx.add_nanocross()
        except Exception:
            await ctx.send(Exception)
    
    @blacklist.command(
        name = "all",
        brief = "Sends all blacklisted users.")
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def blacklisted_all(self, ctx: GeraltContext) -> typing.Optional[discord.Message]:
        """Get a list of blacklisted members."""
        query = "SELECT user_id, reason, queried_at, jump_url FROM blacklist"
        fetched_blacklisted_members = await self.bot.db.fetch(query)
        blacklisted_members = []
        serial_no = 1
        for data in fetched_blacklisted_members:
            user = await self.bot.fetch_user(data[0])
            blacklisted_members.append(f"> [**{serial_no}).**]({data[3]}) ─ **{user}** (`{data[0]}`)\n> │ ` ─ ` Reason : \"{data[1]}\"\n> │ ` ─ ` Blacklisted : {self.bot.timestamp(data[2], style = 'R')}\n────\n")
            serial_no += 1
        if not fetched_blacklisted_members:
            await ctx.reply("Seems like you haven't blacklisted anyone \U0001f440")
        else:
            if serial_no <= 2:
                blacklisted_emb = BaseEmbed(
                    title = f"\U0001f4dc Blacklisted Users",
                    description = f"".join(blacklisted_members),
                    colour = self.bot.colour)
                await ctx.reply(embed = blacklisted_emb, mention_author = False)
            else:
                embed_list = []
                while blacklisted_members:
                    blacklisted_emb = BaseEmbed(
                        title = f"\U0001f4dc Blacklisted Users",
                        description = f"".join(blacklisted_members[:2]),
                        colour = self.bot.colour)
                    blacklisted_members = blacklisted_members[2:]
                    embed_list.append(blacklisted_emb)
                await Paginator(self.bot, ctx, embeds = embed_list).send(ctx)
    
    @commands.command(
        name = "self-purge")
    @commands.is_owner()
    async def de(self, ctx: GeraltContext, limit: int = None) -> typing.Optional[discord.Message]:
        """Delete a referenced message or purge few."""
        if ctx.message.reference and ctx.message.reference.resolved.author == self.bot.user:
            await ctx.message.reference.resolved.delete()
            try:
                await ctx.message.delete()
                await ctx.add_nanotick()
            except Exception as exception:
                await ctx.send(f"```py\{exception}\n```")
                await ctx.add_nanocross()
        if not limit:
            limit = 10
        await ctx.channel.purge(limit = limit, check = lambda u: u.author == self.bot.user, bulk = False)
        try:
            await ctx.message.delete()
            await ctx.add_nanotick()
        except Exception as exception:
            await ctx.send(f"```py\{exception}\n```")
            await ctx.add_nanocross()