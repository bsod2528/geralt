import datetime
import io
import os
import re
import sys
import time
import traceback
from collections import defaultdict
from typing import Any, DefaultDict, Dict, List, Optional, Set, Tuple

import aiohttp
import asyncpg
import discord
import dotenv
import humanize
from aiogithub import GitHub
from discord import app_commands
from discord.ext import commands
from dotenv import dotenv_values

from .context import BaseContext
from .embed import BaseEmbed
from .kernel.utilities import override_jsk
from .kernel.utilities.crucial import WebhookManager
from .kernel.utilities.extensions import COGS_EXTENSIONS
from .kernel.utilities.reports import ensure_report_tables
from .kernel.views.meta import Info
from .kernel.web import DashboardAPI

dotenv.load_dotenv()
os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"

CONFIG = dotenv_values("config.env")
TOKEN = CONFIG.get("TOKEN")
DB_URL = CONFIG.get("DB_URL")
EMOTE_TO_URL = re.compile(
    r"(https?://)?(media|cdn)\.discord(app)?\.(com|net)/emojis/(?P<id>[0-9]+)\.(?P<fmt>[A-z]+)"
)

escape: str = "\x1b"

# BSOD#0067 [ME], SID#1380 [Zeus432]]
DEVELOPER_IDS: List[int] = [750979369001811982, 760823877034573864]


class BaseBot(commands.Bot):
    """Geralt's subclass of :class: `commands.Bot`.

    Attributes:
    ----------
    db: `asyncpg.Pool`
        Allows communication between self and database.
    git: `None`
        Allows communication between self and Github
    colour: `discord.Colour`
        A standard colour for most embeds
    mentions: `discord.AllowedMentions`
        Set to `None` so that no one is mentioned in a message.
    no_prefix: `bool`
        Var for enabling/disabling the no prefix functionality.
    timestamp: `function`
        Getting the timestamp at the moment.
    github_token: `str`
        BSOD's Github Personal Access Token.
    webhook_manager: `geralt.WebhookManager`
        Takes care of all actions that utilise discord's Webhooks.
    developer_mode: `bool`
        Var for enabling/disabling the developer mode functionality.
    add_persistent_views: `bool`
        For adding persistent views.

    Caching Attributes:
    -------------------
    afk: `Dict[int, Tuple[str, datetime.datetime]]`
        Stores user ids mapped to their afk reason and the timestamp it was set.
    meta: `Dict[int, List[int]]`
        Stores number of what commands have been used in a guild.
    prefixes: DefaultDict[int, typing.Set[str]]
        Used for caching the prefixes rather than querying the database each time.
    blacklists: `Set[discord.Object.id]`
        Stores all object ids which have been blacklisted.
    highlight: `Dict[int, Dict[int, List[str]]]`
        Has a list of triggers for a user for each guild.
    ticket_init: `Dict[int, List[Any]]`
        Stores information for posting the ticket panel.
    verification: `Dict[int, List]`
        Stors information for posting the verification panel.
    ticket_kernel: `Dict[int, List[int]]`
        Stores the opened ticket information for each guild.
    highlight_blocked: `Dict[int, Dict[int, List[int]]]`
        Stores a list of object ids blocked by a user in a guild.
    locked_objects_ids: `List[int]`
        Stores a list of ids of locked channels.
    convert_url_to_webhook: `Dict[int, str]`
        A dictionary of bool values in str for converting url emotes to webhook.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            status=discord.Status.online,
            intents=discord.Intents.all(),
            tree_cls=app_commands.CommandTree,
            activity=discord.Activity(
                type=discord.ActivityType.playing, name="Waking up to Die"
            ),
            command_prefix=self.get_prefix,
            case_insensitive=True,
            strip_after_prefix=True,
            *args,
            **kwargs,
        )

        self.db: asyncpg.Pool = None
        self.git = None
        self.config = CONFIG
        self.colour = discord.Colour.from_rgb(170, 179, 253)
        self.mentions = discord.AllowedMentions.none()
        self.no_prefix: bool = False
        self.timestamp = discord.utils.format_dt
        self.owner_ids: List = DEVELOPER_IDS
        self.github_token: str = CONFIG.get("GITHUB_TOKEN")
        self.snipe_counter: Dict[int, Dict[str, int]] = {}
        self.webhook_manager = WebhookManager()
        self.developer_mode: bool = False
        self.add_persistent_views = False
        self.dashboard_api: DashboardAPI | None = None

        # Attributes for caching.
        self.afk: Dict[int, Tuple[str, datetime.datetime]] = {}
        self.meta: Dict[int, List[int]] = {}
        self.prefixes: DefaultDict[int, Set[str]] = defaultdict(set)
        self.blacklists: Set[discord.Object.id] = set()  # type: ignore
        self.highlight: Dict[int, Dict[int, List[Dict[str, Any]]]] = {}
        self.ticket_init: Dict[int, List[Any]] = {}
        self.verification: Dict[int, List] = {}
        self.ticket_kernel: Dict[int, List] = {}
        self.highlight_blocked: Dict[int, Dict[int, List]] = {}
        self.locked_objects_ids: List[int] = []
        self.settings: Dict[int, Dict[str, bool]] = {}
        self.highlight_preferences: Dict[int, Dict[int, Dict[str, Any]]] = {}
        self.highlight_digest_cache: Dict[int, Dict[int, List[Dict[str, Any]]]] = {}
        self.snipe_retention_settings: Dict[int, Dict[str, Any]] = {}

    def __repr__(self) -> str:
        return "BaseBot"

    # Credits to qt_haskell [ Lia Marie ] - *sobs*
    def generate_dict_cache(
        self, entries: List[Tuple]
    ) -> Dict[int, Dict[int, List[Any]]]:
        """Generates a dict with the following structure:

        x = {
            int: {
                int: list[Any]
                }
            }"""
        cache: Dict = {}
        for entry in entries:
            guild_id, parent, children = entry
            if guild_id not in cache:
                cache[guild_id]: Dict = {}  # type: ignore
            if parent not in cache[guild_id]:
                cache[guild_id][parent]: List = []  # type: ignore
            cache[guild_id][parent].append(children)
        return cache

    async def get_context(
        self, message: discord.Message, *, cls=BaseContext
    ) -> BaseContext:
        """Return the custom :class:`~geralt.context.BaseContext` type."""

        return await super().get_context(message, cls=cls)

    async def on_error(self, event_method: str, *args: Any, **kwargs: Any) -> None:
        """Post traceback details to the configured error webhook."""

        traceback_string = "".join(
            traceback.format_exception(*(einfo := sys.exc_info()))
        )
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.partial(
                id=CONFIG.get("ERROR_ID"),
                token=CONFIG.get("ERROR_TOKEN"),
                session=session,
            )
            await webhook.send(
                f"An error occurred in an `{event_method}` event",
                file=discord.File(
                    io.BytesIO(traceback_string.encode()), filename="traceback.py"
                ),
            )
            await webhook.send("|| Break Point ||")
        await session.close()

    async def get_prefix(self, message: discord.Message):
        """Determine the prefixes applicable for the supplied message."""

        if self.no_prefix is True and message.author.id in self.owner_ids:
            return ""
        cached = self.prefixes.get((message.guild and message.guild.id), None)
        if cached is not None:
            prefix = set(cached)
        else:
            prefix = {
                ".g",
            }
        if not prefix:
            prefix = {".g"}
        return commands.when_mentioned_or(*prefix)(self, message)

    # db connection
    async def connect_to_database(self):
        """Connects to the database."""
        try:
            print(
                f"{escape}[0;1;37;40m > {escape}[0m {escape}[0;1;35m──{escape}[0m {escape}[0;1;36m{time.strftime('%c', time.localtime())}{escape}[0;1;36m ─ Waking up{escape}[0m"
            )
            print(
                f"{escape}[0;1;37;40m > {escape}[0m {escape}[0;1;35m──{escape}[0m {escape}[0;1;34m{time.strftime('%c', time.localtime())}{escape}[0;1;34m ─ Establishing connection with my database.{escape}[0m"
            )

            # Thank you LeoCx1000 for this :D
            def _encode_jsonb(value: Any) -> Any:
                return discord.utils._to_json(value)

            def _decode_jsonb(value: Any) -> Any:
                return discord.utils._from_json(value)

            async def init(connection: Any):
                await connection.set_type_codec(
                    "jsonb",
                    schema="pg_catalog",
                    encoder=_encode_jsonb,
                    decoder=_decode_jsonb,
                    format="text",
                )

            self.db = await asyncpg.create_pool(
                DB_URL,
                init=init,
            )
            await ensure_report_tables(self.db)
            print(
                f"{escape}[0;1;37;40m > {escape}[0m {escape}[0;1;35m──{escape}[0m {escape}[0;1;32m{time.strftime('%c', time.localtime())}{escape}[0;1;32m ─ Connection established successfully.{escape}[0m"
            )
        except Exception as exception:
            i = "".join(
                traceback.format_exception(
                    type(exception), exception, exception.__traceback__
                )
            )
            return print(i)
            return print(
                f"{escape}[0;1;37;40m > {escape}[0m {escape}[0;1;35m──{escape}[0;1;31m{time.strftime('%c', time.localtime())}{escape}[0;1;31m ─ Couldnt connect due to : {exception}{escape}[0m"
            )

    async def ensure_snipe_infrastructure(self) -> None:
        """Create tables required for snipe analytics if they are missing."""

        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS snipe_retention_settings (
                guild_id BIGINT PRIMARY KEY,
                retention_days INTEGER NOT NULL DEFAULT 30,
                anonymize_attachments BOOLEAN NOT NULL DEFAULT FALSE,
                analytics_opt_out BOOLEAN NOT NULL DEFAULT FALSE,
                attachment_opt_out BOOLEAN NOT NULL DEFAULT FALSE
            )
            """
        )
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS snipe_metrics (
                guild_id BIGINT NOT NULL,
                captured_on DATE NOT NULL,
                total_messages BIGINT NOT NULL DEFAULT 0,
                delete_count BIGINT NOT NULL DEFAULT 0,
                edit_count BIGINT NOT NULL DEFAULT 0,
                PRIMARY KEY (guild_id, captured_on)
            )
            """
        )

    # load extensions
    async def load_all_extensions(self):
        """Load every extension listed in :data:`COGS_EXTENSIONS`."""

        print(
            f"{escape}[0;1;37;40m > {escape}[0m {escape}[0;1;35m──{escape}[0m {escape}[0;1;34m{time.strftime('%c', time.localtime())}{escape}[0;1;34m ─ Loading all Extensions.{escape}[0m"
        )
        for extensions in COGS_EXTENSIONS:
            try:
                await self.load_extension(extensions)
                print(
                    f"{escape}[0;1;37;40m > {escape}[0m    {escape}[0;1;37m└── {escape}[0;1;30m{time.strftime('%c', time.localtime())}{escape}[0;1;31m  {escape}[0m{escape}[0;1;37m└── {escape}[0m{escape}[0;1;32mLoaded{escape}[0m{escape}[0;1;37m: {escape}[0m{escape}[0;1;35m{extensions} {escape}[0m"
                )
            except Exception as exception:
                print(
                    f"{escape}[0;1;37;40m > {escape}[0m    {escape}[0;1;31m└──{escape}[0m {escape}[0;1;30m{time.strftime('%c', time.localtime())}{escape}[0;1;31m  └── Error Loading: {exception} {escape}[0m"
                )
        print(
            f"{escape}[0;1;37;40m > {escape}[0m {escape}[0;1;35m──{escape}[0m {escape}[0;1;32m{time.strftime('%c', time.localtime())} ─ Extensions Successfully Loaded.{escape}[0m"
        )

    # load cache from db
    async def load_cache(self):
        """Hydrate in-memory caches from the persistent database."""

        afk_data = await self.db.fetch("SELECT * FROM afk")
        meta_data = await self.db.fetch("SELECT * FROM meta")
        snipe_data = await self.db.fetch(
            "SELECT * FROM guild_settings WHERE snipe = True"
        )
        prefix_data = await self.db.fetch("SELECT guild_id, prefixes FROM prefix")
        guild_settings = await self.db.fetch("SELECT * FROM guild_settings")
        retention_settings = await self.db.fetch(
            "SELECT * FROM snipe_retention_settings"
        )
        highlight_data = await self.db.fetch("SELECT * FROM highlight")
        ticket_init_data = await self.db.fetch("SELECT * FROM ticket_init")
        verification_data = await self.db.fetch("SELECT * FROM verification")
        blacklisted_objects = await self.db.fetch("SELECT snowflake_id FROM blacklist")
        ticket_kernel_data = await self.db.fetch("SELECT * FROM ticket_kernel")
        highlight_blocked_data = await self.db.fetch("SELECT * FROM highlight_blocked")
        locked_objects_ids_data = await self.db.fetch("SELECT * FROM channel_lock")
        try:
            highlight_preferences_data = await self.db.fetch(
                "SELECT * FROM highlight_preferences"
            )
        except asyncpg.UndefinedTableError:
            highlight_preferences_data = []

        self.afk = {
            data["user_id"]: (data["reason"], data["queried_at"])
            for data in afk_data
        }
        self.meta = {
            data["guild_id"]: [data["command_name"], data["invoked_at"], data["uses"]]
            for data in meta_data
        }
        self.ticket_init = {
            data["guild_id"]: [
                data["category_id"],
                data["sent_channel_id"],
                data["sent_message_id"],
                data["jump_url"],
                data["panel_description"],
                data["id"],
            ]
            for data in ticket_init_data
        }
        self.verification = {
            data["guild_id"]: [
                data["question"],
                data["answer"],
                data["role_id"],
                data["channel_id"],
                data["message_id"],
            ]
            for data in verification_data
        }
        self.settings = {
            data["guild_id"]: {
                "convert_url_to_webhook": data["convert_url_to_webhook"],
                "snipe": data["snipe"],
            }
            for data in guild_settings
        }

        default_retention = {
            "retention_days": 30,
            "anonymize_attachments": False,
            "analytics_opt_out": False,
            "attachment_opt_out": False,
        }
        self.snipe_retention_settings = {
            data["guild_id"]: {
                "retention_days": data["retention_days"],
                "anonymize_attachments": data["anonymize_attachments"],
                "analytics_opt_out": data["analytics_opt_out"],
                "attachment_opt_out": data["attachment_opt_out"],
            }
            for data in retention_settings
        }

        self.snipe_counter = {
            data["guild_id"]: {"delete": 0, "edit": 0, "total_messages": 0}
            for data in snipe_data
        }

        for guild_id in self.settings.keys():
            self.snipe_retention_settings.setdefault(guild_id, default_retention.copy())

        self.blacklists.update(
            int(record["snowflake_id"]) for record in blacklisted_objects
        )

        if ticket_kernel_data:
            ticket_kernel_list: List[Tuple] = [
                (data["guild_id"], data["ticket_id"], data["invoker_id"])
                for data in ticket_kernel_data
            ]
            self.ticket_kernel = self.generate_dict_cache(ticket_kernel_list)

        if highlight_data:
            highlight_data_list: List[Tuple[int, int, Dict[str, Any]]] = []
            for data in highlight_data:
                highlight_record = dict(data)
                trigger_payload: Dict[str, Any] = {
                    "trigger": highlight_record.get("trigger"),
                    "scope_type": highlight_record.get("scope_type"),
                    "scope_id": highlight_record.get("scope_id"),
                    "snooze_until": highlight_record.get("snooze_until"),
                    "digest": highlight_record.get("digest"),
                }
                highlight_data_list.append(
                    (data["guild_id"], data["user_id"], trigger_payload)
                )
            self.highlight = self.generate_dict_cache(highlight_data_list)
        else:
            self.highlight = {}

        if highlight_blocked_data:
            highlight_blocked_data: List[Tuple] = [
                (data["guild_id"], data["user_id"], data["object_id"])
                for data in highlight_blocked_data
            ]
            self.highlight_blocked = self.generate_dict_cache(highlight_blocked_data)
        else:
            self.highlight_blocked = {}

        if highlight_preferences_data:
            preference_cache: Dict[int, Dict[int, Dict[str, Any]]] = {}
            for record in highlight_preferences_data:
                preference_record = dict(record)
                guild_dict = preference_cache.setdefault(record["guild_id"], {})
                guild_dict[record["user_id"]] = {
                    "digest": preference_record.get("digest", "immediate"),
                    "next_dispatch": preference_record.get("next_dispatch"),
                }
            self.highlight_preferences = preference_cache
        else:
            self.highlight_preferences = {}

        self.locked_objects_ids.extend(
            int(data["object_id"]) for data in locked_objects_ids_data
        )

        for guild_id, prefixes in prefix_data:
            # Normalise the stored prefixes so downstream consumers always
            # receive at least the default prefix.
            self.prefixes[guild_id] = set(prefixes) or {
                ".g",
            }

    async def setup_hook(self) -> None:
        """Run post-login setup tasks prior to connecting the websocket."""

        self.session: aiohttp.ClientSession = aiohttp.ClientSession()
        self.tree.copy_global_to(guild=discord.Object(id=CONFIG.get("BSODsThings")))
        self.git = GitHub(self.github_token)

        await self.connect_to_database()
        await self.ensure_snipe_infrastructure()
        await self.load_all_extensions()
        await self.load_cache()

        api_host = CONFIG.get("DASHBOARD_API_HOST") or "0.0.0.0"
        raw_port = CONFIG.get("DASHBOARD_API_PORT")
        try:
            api_port = int(raw_port) if raw_port else 8080
        except (TypeError, ValueError):
            api_port = 8080

        self.dashboard_api = DashboardAPI(self)
        await self.dashboard_api.start(host=api_host, port=api_port)

        if not hasattr(self, "uptime"):
            self.uptime = discord.utils.utcnow()

    async def on_ready(self):
        """Prepare persistent UI views and broadcast startup presence."""

        if not self.add_persistent_views:
            self.add_view(Info(self, BaseContext))
            self.add_persistent_views = True

        async with aiohttp.ClientSession() as session:
            wbhk = discord.Webhook.partial(
                id=CONFIG.get("NOTIF_ID"),
                token=CONFIG.get("NOTIF_TOKEN"),
                session=session,
            )
            await self.change_presence(
                status=discord.Status.idle,
                activity=discord.Activity(
                    type=discord.ActivityType.listening, name=f".ghelp"
                ),
            )
            # await wbhk.send(f"|| Break Point ||\n───\n<:GeraltRightArrow:904740634982760459> Came alive at ─ {self.timestamp(discord.utils.utcnow(), style = 'F')} Hi <a:Waves:920726389869641748>\n```prolog\n"
            # f"No. of Users ─ {len(list(self.get_all_members()))}\nNo. of Guilds ─ {len(self.guilds)}\nWoke up at ─ {time.strftime('%c', time.gmtime())}```")
            print(
                f"{escape}[0;1;37;40m > {escape}[0m {escape}[0;1;35m──{escape}[0m {escape}[0;1;36m{time.strftime('%c', time.localtime())} ─ Awakened{escape}[0m"
            )
            await session.close()

    async def on_message(self, message: discord.Message):
        """Handle bookkeeping for AFK reminders and developer-only mode."""

        await self.wait_until_ready()

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
            reason, timestamp = self.afk.get(message.author.id, (None, None))
            if reason is None:
                reason = "Not Specified . . ."
            if timestamp is None:
                timestamp = discord.utils.utcnow()

            current_time = discord.utils.utcnow() - timestamp
            await message.reply(
                f'Welcome back <a:Waves:920726389869641748>. You were afk:\n>>> <:ReplyContinued:930634770004725821>` ─ ` for: "**{humanize.naturaldelta(current_time)}**"\n<:Reply:930634822865547294>` ─ ` reason: {reason}',
                allowed_mentions=self.mentions,
            )
            await self.db.execute(
                "DELETE FROM afk WHERE user_id = $1", message.author.id
            )
            self.afk.pop(message.author.id, None)

        for pinged_user in message.mentions:
            if pinged_user.id in self.afk:
                reason, timestamp = self.afk.get(pinged_user.id, (None, None))

                if reason is None:
                    reason = "Not Specified . . ."
                if timestamp is None:
                    timestamp = discord.utils.utcnow()

                current_time = discord.utils.utcnow() - timestamp
                await message.reply(
                    f"<:Join:932976724235395072> **{pinged_user}** has been afk:\n>>> <:ReplyContinued:930634770004725821>` ─ ` for: {reason}\n<:Reply:930634822865547294>` ─ ` since: {humanize.naturaldelta(current_time)}"
                )

        if message.content in [self.user.mention]:
            prefix_emb = BaseEmbed(
                description=f"> <:GeraltRightArrow:904740634982760459> "
                + "\n> <:GeraltRightArrow:904740634982760459> ".join(
                    await self.get_prefix(message)
                ),
                colour=self.colour,
            )
            prefix_emb.set_footer(text="Run `@Geralthelp prefix`.")
            if message.guild.icon.url:
                prefix_emb.set_author(
                    name=f"{len(await self.get_prefix(message))} Prefixes ─ {message.guild}",
                    icon_url=message.guild.icon.url,
                )
            else:
                prefix_emb.set_author(name=message.guild)
            return await message.reply(embed=prefix_emb, mention_author=False)

        await self.process_commands(message)

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Invokes command [if needed] on editing a message"""
        if after.content != before.content:
            ctx: BaseContext = await self.get_context(after)
            await self.invoke(ctx)

    def dashboard_url(self, guild: discord.Guild | None = None) -> str:
        base = CONFIG.get("DASHBOARD_BASE_URL") or "https://bsod2528.github.io/pages/projects/geralt/geralt.html"
        base = base.rstrip("/")
        if guild is not None:
            return f"{base}/guilds/{guild.id}/settings"
        return base

    def guild_configuration_snapshot(self, guild_id: int) -> Dict[str, Any]:
        prefixes = sorted(self.prefixes.get(guild_id, {".g"}))

        highlight_map = self.highlight.get(guild_id, {})
        highlight = [
            {"user_id": user_id, "triggers": sorted(set(triggers))}
            for user_id, triggers in highlight_map.items()
        ]

        highlight_blocked_map = self.highlight_blocked.get(guild_id, {})
        highlight_blocked = [
            {"user_id": user_id, "object_ids": sorted({*object_ids})}
            for user_id, object_ids in highlight_blocked_map.items()
        ]

        ticket_cache = self.ticket_init.get(guild_id)
        ticket_panel: Optional[Dict[str, Any]] = None
        if ticket_cache:
            ticket_panel = {
                "category_id": ticket_cache[0],
                "sent_channel_id": ticket_cache[1],
                "sent_message_id": ticket_cache[2],
                "jump_url": ticket_cache[3],
                "panel_description": ticket_cache[4],
                "id": ticket_cache[5] if len(ticket_cache) > 5 else None,
            }

        verification_cache = self.verification.get(guild_id)
        verification_panel: Optional[Dict[str, Any]] = None
        if verification_cache:
            verification_panel = {
                "question": verification_cache[0],
                "answer": verification_cache[1],
                "role_id": verification_cache[2],
                "channel_id": verification_cache[3],
                "message_id": verification_cache[4],
            }

        flags = self.settings.get(
            guild_id,
            {"convert_url_to_webhook": False, "snipe": False},
        )

        return {
            "guild_id": guild_id,
            "prefixes": prefixes,
            "highlight": highlight,
            "highlight_blocked": highlight_blocked,
            "ticket_panel": ticket_panel,
            "verification_panel": verification_panel,
            "flags": flags,
        }

    async def close(self) -> None:
        if self.dashboard_api is not None:
            await self.dashboard_api.stop()
            self.dashboard_api = None
        if hasattr(self, "session") and not self.session.closed:
            await self.session.close()
        await super().close()


geralts_instance = BaseBot()

discord.utils.setup_logging()


async def run():
    """Starts the bot instance!"""
    async with geralts_instance:
        await geralts_instance.start(TOKEN)
