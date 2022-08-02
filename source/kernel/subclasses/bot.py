import io
import re
import os
import sys
import time
import dotenv
import discord
import asyncpg
import aiohttp
import humanize
import wavelink
import traceback

from aiogithub import GitHub
from dotenv import dotenv_values
from wavelink.ext import spotify
from discord import app_commands
from discord.ext import commands
from collections import defaultdict
from typing import Any, Set, List, Dict, Union, Optional, DefaultDict

from .embed import BaseEmbed
from ..views.meta import Info
from .context import GeraltContext
from ..utilities.crucial import WebhookManager
from ..utilities.extensions import COGS_EXTENSIONS

import source.kernel.utilities.override_jsk

dotenv.load_dotenv()
os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"

CONFIG = dotenv_values("config.env")
TOKEN = CONFIG.get("TOKEN")
DB_URL = CONFIG.get("DB_URL")
EMOTE_TO_URL = re.compile(
    r"(https?://)?(media|cdn)\.discord(app)?\.(com|net)/emojis/(?P<id>[0-9]+)\.(?P<fmt>[A-z]+)")

escape: str = "\x1b"

# BSOD#0067 [ME]      SID#1380 [Zeus432]
DEVELOPER_IDS = [750979369001811982, 760823877034573864]


class Geralt(commands.Bot):
    """Geralt's subclass of :class: `commands.Bot`."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            status=discord.Status.online,
            intents=discord.Intents.all(),
            tree_cls=app_commands.CommandTree,
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name="Waking up to Die"),
            command_prefix=self.get_prefix,
            case_insensitive=True,
            strip_after_prefix=True,
            *args,
            **kwargs)

        self.db: asyncpg.pool
        self.git = None
        self.colour = discord.Colour.from_rgb(170, 179, 253)
        self.mentions = discord.AllowedMentions.none()
        self.no_prefix: bool = False
        self.timestamp = discord.utils.format_dt
        self.owner_ids: List = DEVELOPER_IDS
        self.github_token: str = CONFIG.get("GITHUB_TOKEN")
        self.developer_mode: bool = False
        self.add_persistent_views = False
        self.webhook_manager = WebhookManager()

        # Attributes for caching.
        self.afk: Dict = {}
        self.meta: Dict = {}
        self.prefixes: DefaultDict[int, Set[str]] = defaultdict(set)
        self.blacklists: Dict = set()
        self.ticket_init: Dict = {}
        self.verification: Dict = {}
        self.ticket_kernel: Dict = {}
        self.locked_objects_ids: List = []
        self.convert_url_to_webhook: Dict = {}

    def __repr__(self) -> str:
        return "<Bot>"

    async def get_context(self, message: discord.Message, *, cls=GeraltContext) -> GeraltContext:
        return await super().get_context(message, cls=cls)

    async def on_error(self, event_method: str, *args: Any, **kwargs: Any) -> None:
        traceback_string = "".join(
            traceback.format_exception(*(einfo := sys.exc_info())))
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.partial(
                id=CONFIG.get("ERROR_ID"),
                token=CONFIG.get("ERROR_TOKEN"),
                session=session)
            await webhook.send(f"An error occurred in an `{event_method}` event", file=discord.File(io.BytesIO(traceback_string.encode()), filename="traceback.py"))
            await webhook.send("|| Break Point ||")
        await session.close()

    async def get_prefix(self, message: discord.Message):
        if self.no_prefix is True and message.author.id in self.owner_ids:
            return ""
        cached = self.prefixes.get(
            (message.guild and message.guild.id),
            None)  # type: ignore
        if cached is not None:
            prefix = set(cached)
        else:
            prefix = {".g", }
        if not prefix:
            prefix = {".g"}
        return commands.when_mentioned_or(*prefix)(self, message)

    # Connects to Lavalink server.
    async def connect_to_lavalink(self):
        try:
            await wavelink.NodePool.create_node(
                bot=self,
                host="127.0.0.1",
                port=2333,
                password=CONFIG.get("LAVALINK"),
                spotify_client=spotify.SpotifyClient(client_id=CONFIG.get("SPOTIFY_ID"), client_secret=CONFIG.get("SPOTIFY_SECRET")))
        except Exception as exception:
            print(f"{escape}[0;1;37;40m > {escape}[0m {escape}[0;1;35m──{escape}[0m {escape}[0;1;31m{time.strftime('%c', time.localtime())} ─ {exception} : {exception}\n{escape}[0m")
            return

    # DB connection
    async def connect_to_database(self):
        try:
            print(f"{escape}[0;1;37;40m > {escape}[0m {escape}[0;1;35m──{escape}[0m {escape}[0;1;36m{time.strftime('%c', time.localtime())} ─ Waking up{escape}[0m")
            print(f"{escape}[0;1;37;40m > {escape}[0m {escape}[0;1;35m──{escape}[0m {escape}[0;1;34m{time.strftime('%c', time.localtime())} ─ Establishing connection with my database.{escape}[0m")
            self.db = await asyncpg.create_pool(dsn=DB_URL)
            print(f"{escape}[0;1;37;40m > {escape}[0m {escape}[0;1;35m──{escape}[0m {escape}[0;1;32m{time.strftime('%c', time.localtime())} ─ Connection established successfully.{escape}[0m")
        except Exception as exception:
            print(f"{escape}[0;1;37;40m > {escape}[0m {escape}[0;1;35m──{escape}[0;1;31m{time.strftime('%c', time.localtime())} ─ Couldnt connect due to : {exception}{escape}[0m")

    # Load extensions.
    async def load_all_extensions(self):
        print(f"{escape}[0;1;37;40m > {escape}[0m {escape}[0;1;35m──{escape}[0m {escape}[0;1;34m{time.strftime('%c', time.localtime())} ─ Loading all Extensions.{escape}[0m")
        for extensions in COGS_EXTENSIONS:
            try:
                await self.load_extension(extensions)
            except Exception as exception:
                print(f"{escape}[0;1;37;40m > {escape}[0m {escape}[0;1;35m──{escape}[0m {escape}[0;1;31m{time.strftime('%c', time.localtime())} ─ {exception} : {exception}\n{escape}[0m")
        print(f"{escape}[0;1;37;40m > {escape}[0m {escape}[0;1;35m──{escape}[0m {escape}[0;1;32m{time.strftime('%c', time.localtime())} ─ Extensions Successfully Loaded.{escape}[0m")

    async def setup_hook(self) -> None:
        self.tree.copy_global_to(
            guild=discord.Object(
                id=CONFIG.get("BSODsThings")))
        self.git = GitHub(self.github_token)

        await self.connect_to_database()
        await self.load_all_extensions()

        if not hasattr(self, "uptime"):
            self.uptime = discord.utils.utcnow()

    async def cache_stuff(self):
        afk_deets = await self.db.fetch("SELECT * FROM afk")
        meta_deets = await self.db.fetch("SELECT * FROM meta")
        prefix_deets = await self.db.fetch("SELECT guild_id, guild_prefix FROM prefix")
        ticket_init_deets = await self.db.fetch("SELECT * FROM ticket_init")
        verification_deets = await self.db.fetch("SELECT * FROM verification")
        ticket_kernel_deets = await self.db.fetch("SELECT * FROM ticket_kernel")
        locked_objects_ids_deets = await self.db.fetch("SELECT * FROM channel_lock")
        convert_url_to_webhook_deets = await self.db.fetch("SELECT * FROM guild_settings")

        self.afk = {data["user_id"]: data["reason"] for data in afk_deets}
        self.meta = {
            data["guild_id"]: [
                data["command_name"],
                data["invoked_at"],
                data["uses"]] for data in meta_deets}
        self.ticket_kernel = {
            data["guild_id"]: [
                data["ticket_id"],
                data["invoker_id"],
                data["invoked_at"]] for data in ticket_kernel_deets}
        self.ticket_init = {
            data["guild_id"]: [
                data["category_id"],
                data["sent_channel_id"],
                data["sent_message_id"],
                data["jump_url"],
                data["panel_description"],
                data["message_description"],
                data["id"]] for data in ticket_init_deets}
        self.verification = {
            data["guild_id"]: [
                data["question"],
                data["answer"],
                data["role_id"],
                data["channel_id"],
                data["message_id"]] for data in verification_deets}
        self.convert_url_to_webhook = {
            data["guild_id"]: data["convert_url_to_webhook"] for data in convert_url_to_webhook_deets}

        self.locked_objects_ids.append(
            data["object_id"] for data in locked_objects_ids_deets)

        for guild_id, prefixes in prefix_deets:
            self.prefixes[guild_id] = set(prefixes) or {".g", }

    async def on_ready(self):

        await self.cache_stuff()
        # await self.connect_to_lavalink()

        if not self.add_persistent_views:
            self.add_view(Info(self, GeraltContext))
            self.add_persistent_views = True

        fetch_blacklisted_objects = await self.db.fetch("SELECT snowflake FROM blacklist")
        self.blacklists.add(objects for objects in fetch_blacklisted_objects)

        async with aiohttp.ClientSession() as session:
            wbhk = discord.Webhook.partial(
                id=CONFIG.get("NOTIF_ID"),
                token=CONFIG.get("NOTIF_TOKEN"),
                session=session)
            await self.change_presence(
                status=discord.Status.idle,
                activity=discord.Activity(type=discord.ActivityType.listening, name=f".ghelp"))
            await wbhk.send(f"|| Break Point ||\n───\n<:GeraltRightArrow:904740634982760459> Came alive at ─ {self.timestamp(discord.utils.utcnow(), style = 'F')} Hi <a:Waves:920726389869641748>\n```prolog\n"
                            f"No. of Users ─ {len(list(self.get_all_members()))}\nNo. of Guilds ─ {len(self.guilds)}\nWoke up at ─ {time.strftime('%c', time.gmtime())}```")
            print(f"{escape}[0;1;37;40m > {escape}[0m {escape}[0;1;35m──{escape}[0m {escape}[0;1;36m{time.strftime('%c', time.localtime())} ─ Awakened{escape}[0m")
            await session.close()

    async def on_message(self, message: discord.Message):
        await self.wait_until_ready()
        afk_deets = await self.db.fetch("SELECT * FROM afk")

        try:
            if message.author.id in self.blacklists:
                return
        except AttributeError:
            return

        try:
            if message.channel.id in self.blacklists:
                return
        except AttributeError:
            return

        try:
            if message.guild.id in self.blacklists:
                return
        except AttributeError:
            return

        if self.developer_mode is True:
            if message.author.id in self.owner_ids:
                await self.change_presence(status=discord.Status.invisible)
                return await self.process_commands(message)
            return

        if message.author.id in self.afk:
            for user in afk_deets:
                time = user["time"]
                reason = user["reason"]
            current_time = discord.utils.utcnow() - time
            await message.reply(f"Welcome back <a:Waves:920726389869641748>. You were afk :\n>>> <:ReplyContinued:930634770004725821>` ─ ` for : \"**{humanize.naturaldelta(current_time)}**\"\n<:Reply:930634822865547294>` ─ ` reason : {reason}", allowed_mentions=self.mentions)
            await self.db.execute("DELETE FROM afk WHERE user_id = $1", message.author.id)
            try:
                self.afk.pop(message.author.id)
            except KeyError:
                return

        for pinged_user in message.mentions:
            if pinged_user.id in self.afk:
                for data in afk_deets:
                    time = data["time"]
                    reason = data["reason"]
                    current_time = discord.utils.utcnow() - time
                await message.reply(f"<:Join:932976724235395072> **{pinged_user}** has been afk :\n>>> <:ReplyContinued:930634770004725821>` ─ ` for : {reason}\n<:Reply:930634822865547294>` ─ ` since : {humanize.naturaldelta(current_time)}")

        if message.content in [self.user.mention]:
            prefix_emb = BaseEmbed(
                description="\n".join(await self.get_prefix(message)),
                colour=self.colour)
            prefix_emb.set_footer(text="Run `@Geralthelp prefix`.")
            if message.guild.icon.url:
                prefix_emb.set_author(name=f"{len(await self.get_prefix(message))} Prefixes ─ {message.guild}", icon_url=message.guild.icon.url)
            else:
                prefix_emb.set_author(name=message.guild)
            return await message.reply(embed=prefix_emb, mention_author=False)

        await self.process_commands(message)

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Invokes command [if needed] on editing a message"""
        if after.content != before.content:
            return await self.process_commands(after)


Geralt = Geralt()


async def run():
    async with Geralt:
        await Geralt.start(TOKEN)
