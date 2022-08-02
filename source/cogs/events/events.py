import re
import time
import aiohttp
import discord
import wavelink

from discord.ext import commands

from ...kernel.subclasses.embed import BaseEmbed
from ...kernel.subclasses.bot import CONFIG, Geralt
from ...kernel.subclasses.context import GeraltContext

escape: str = "\x1b"
# Thanks a lot Daniel for helping me with the regex :weary:
EMOTE_TO_URL = re.compile(
    r"(https?://)?(media|cdn)\.discord(app)?\.(com|net)/emojis/(?P<id>[0-9]+)\.(?P<fmt>[A-z]+)")


class Events(commands.Cog):
    def __init__(self, bot: Geralt):
        self.bot: Geralt = bot

    @commands.Cog.listener("on_message")
    async def send_emote_url(self, message: discord.Message):
        try:
            try:
                convert_url_to_webhook = self.bot.convert_url_to_webhook[message.guild.id]
            except KeyError:
                convert_url_to_webhook = await self.bot.db.fetchval("SELECT convert_url_to_webhook FROM guild_settings WHERE guild_id = $1", message.guild.id)
        except AttributeError:
            pass
        try:
            if not convert_url_to_webhook:
                return
            if convert_url_to_webhook == "true":
                emote = EMOTE_TO_URL.match(message.content)
                if not emote:
                    return
                emote_id = emote.group("id")
                emote_prefix = {True: "a", False: ""}[
                    emote.group("fmt") == "gif"]

                # type: ignore
                webhook = await self.bot.webhook_manager.fetch_webhook(message.channel)
                await message.delete()
                if message.reference:
                    referenced_message_emb = BaseEmbed(colour=self.bot.colour)
                    referenced_message_emb.add_field(
                        name="Content",
                        value=f"[**{message.reference.resolved.content}**]({message.reference.jump_url})")
                    referenced_message_emb.set_author(name=f"Replying to {message.reference.resolved.author}", icon_url=message.reference.resolved.author.display_avatar)
                    return await webhook.send(
                        content=f"<{emote_prefix}:_:{emote_id}>",
                        embed=referenced_message_emb,
                        avatar_url=message.author.display_avatar.url,
                        username=message.author.display_name)

                await webhook.send(
                    content=f"<{emote_prefix}:_:{emote_id}>",
                    avatar_url=message.author.display_avatar.url,
                    username=message.author.display_name)
        except UnboundLocalError:
            pass

    @commands.Cog.listener("on_message_edit")
    async def edit_to_url(self, before: discord.Message, after: discord.Message):
        try:
            try:
                convert_url_to_webhook = self.bot.convert_url_to_webhook[after.guild.id]
            except KeyError:
                convert_url_to_webhook = await self.bot.db.fetchval("SELECT convert_url_to_webhook FROM guild_settings WHERE guild_id = $1", after.guild.id)
        except AttributeError:
            pass
        try:
            if not convert_url_to_webhook:
                return
            if convert_url_to_webhook == "true":
                emote = EMOTE_TO_URL.match(after.content)
                if not emote:
                    return
                if before.content == after.content:
                    return
                emote_id = emote.group("id")
                emote_prefix = {True: "a", False: ""}[
                    emote.group("fmt") == "gif"]
                # type: ignore
                webhook = await self.bot.webhook_manager.fetch_webhook(after.channel)
                await after.delete()
                if after.reference:
                    referenced_message_emb = BaseEmbed(colour=self.bot.colour)
                    referenced_message_emb.add_field(
                        name="Content",
                        value=f"[**{after.reference.resolved.content}**]({after.reference.jump_url})")
                    referenced_message_emb.set_author(name=f"Replying to {after.reference.resolved.author}", icon_url=after.reference.resolved.author.display_avatar)
                    return await webhook.send(
                        content=f"<{emote_prefix}:_:{emote_id}>",
                        embed=referenced_message_emb,
                        avatar_url=after.author.display_avatar.url,
                        username=after  .author.display_name)
                await webhook.send(
                    content=f"<{emote_prefix}:_:{emote_id}>",
                    avatar_url=after.author.display_avatar.url,
                    username=after.author.display_name)
        except UnboundLocalError:
            pass

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        """Indicates when the node is ready"""
        return print(f"{escape}[0;1;37;40m > {escape}[0m {escape}[0;1;35m──{escape}[0m {escape}[0;1;36m{time.strftime('%c', time.localtime())} ─ Node Identifier : {escape}[0m{escape}[0;1;31m{node.identifier}{escape}[0m")

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: GeraltContext):
        """Stores number of times a command is run [ per guild ]"""
        command_name = ctx.command.root_parent
        if not command_name:
            command_name = ctx.command or ctx.invoked_subcommand
        if not ctx.guild:
            pass
        else:
            query = "INSERT INTO meta ("\
                    "command_name, guild_id, invoked_at, uses)" \
                    "VALUES ($1, $2, $3, 1)" \
                    "ON CONFLICT(command_name, guild_id)" \
                    "DO UPDATE SET uses = meta.uses + 1, invoked_at = $3, command_name = $1"
            await self.bot.db.execute(query, str(command_name), ctx.guild.id, ctx.message.created_at)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """Sends a Webhook upon joining a guild"""
        join_emb = BaseEmbed(
            title=f":scroll: I Joined {guild.name}",
            colour=self.bot.colour)
        join_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> General Information :",
            value=f"> ` ─ ` <a:Owner:905750348457738291> Owner : **{guild.owner}** (`{guild.owner.id}`) \n"
            f"> ` ─ ` <a:Info:905750331789561856> Identification No. : `{guild.id}` \n"
            f"> ` ─ ` <a:Verify:905748402871095336> Verification Level : {str(guild.verification_level).replace('_', ' ').replace('`None`', '`Nill`').title()}")
        join_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Initialisation :",
            value=f"> ` ─ ` <a:Woo:905754435379163176> Made On : {self.bot.timestamp(guild.created_at)} \n"
            f"> ` ─ ` <a:WumpusVibe:905457020575031358> I Joined : {self.bot.timestamp(discord.utils.utcnow())}",
            inline=False)
        async with aiohttp.ClientSession() as session:
            join_log_webhook = discord.Webhook.partial(
                id=CONFIG.get("JOIN_LOG_ID"),
                token=CONFIG.get("JOIN_LOG_TOKEN"),
                session=session)
            await join_log_webhook.send(embed=join_emb)
            await join_log_webhook.session.close()
            await session.close()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        """Sends a Webhook upon being removed from a guild"""
        leave_emb = BaseEmbed(
            title=f":scroll: I Left {guild.name}",
            colour=discord.Colour.from_rgb(255, 97, 142))
        leave_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> General Information :",
            value=f"> ` ─ ` <a:Owner:905750348457738291> Owner : **{guild.owner}** (`{guild.owner.id}`) \n"
            f"> ` ─ ` <a:Info:905750331789561856> Identification No. : `{guild.id}` \n"
            f"> ` ─ ` <a:Verify:905748402871095336> Verification Level : {str(guild.verification_level).replace('_', ' ').replace('`None`', '`Nill`').title()} \n")
        leave_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Initialisation :",
            value=f"> ` ─ ` <a:Woo:905754435379163176> Made On : {self.bot.timestamp(guild.created_at)} \n"
            f"> ` ─ ` <a:PAIN:939876989655994488> I Left : {self.bot.timestamp(discord.utils.utcnow())}",
            inline=False)
        async with aiohttp.ClientSession() as session:
            leave_log_webhook = discord.Webhook.partial(
                id=CONFIG.get("LEAVE_LOG_ID"),
                token=CONFIG.get("LEAVE_LOG_TOKEN"),
                session=session)
            await leave_log_webhook.send(embed=leave_emb)
            await leave_log_webhook.session.close()
