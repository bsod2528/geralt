import asyncio
import datetime
import imghdr
import os
import textwrap
import time
from collections import Counter
from io import BytesIO
from typing import Any, Dict, List, Optional, Union

import aiohttp
import discord
import humanize
from discord import app_commands
from discord.ext import commands, tasks

from ...bot import CONFIG, BaseBot
from ...context import BaseContext
from ...embed import BaseEmbed
from ...kernel.utilities.flags import user_badges, user_perms
from ...kernel.views.meta import PFP
from ...kernel.views.paginator import Paginator
from ...kernel.views.snipe import (
    EditSnipeAttachmentView,
    SnipeAnalyticsView,
    SnipeAttachmentViewer,
    SnipeStats,
)

escape: str = "\x1b"


class Discord(commands.Cog):
    """Commands related to Discord."""

    def __init__(self, bot: BaseBot):
        self.bot = bot
        self.pic_exts = ["png", "jpg", "jpeg", "gif", "bmp", "tiff", "svg"]
        self._default_retention = {
            "retention_days": 30,
            "anonymize_attachments": False,
            "analytics_opt_out": False,
            "attachment_opt_out": False,
        }

    @property
    def emote(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(
            name="Discord", id=930855436670889994, animated=True
        )

    @tasks.loop(minutes=10)
    async def snipe_purge(self):
        self.bot.settings.items()

    @tasks.loop(minutes=30)
    async def snipe_metrics_sync(self) -> None:
        """Persist in-memory snipe counters to the metrics table."""

        if not self.bot.is_ready():
            return

        today = discord.utils.utcnow().date()
        counters = list(self.bot.snipe_counter.items())
        for guild_id, counter in counters:
            if not counter:
                continue

            if not self.analytics_enabled(guild_id):
                self.bot.snipe_counter[guild_id] = {
                    "delete": 0,
                    "edit": 0,
                    "total_messages": 0,
                }
                continue

            delete_count = counter.get("delete", 0)
            edit_count = counter.get("edit", 0)
            total_messages = counter.get("total_messages", 0)

            if delete_count == 0 and edit_count == 0 and total_messages == 0:
                continue

            await self.bot.db.execute(
                """
                INSERT INTO snipe_metrics (guild_id, captured_on, total_messages, delete_count, edit_count)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (guild_id, captured_on)
                DO UPDATE SET
                    total_messages = snipe_metrics.total_messages + EXCLUDED.total_messages,
                    delete_count = snipe_metrics.delete_count + EXCLUDED.delete_count,
                    edit_count = snipe_metrics.edit_count + EXCLUDED.edit_count
                """,
                guild_id,
                today,
                total_messages,
                delete_count,
                edit_count,
            )

            self.bot.snipe_counter[guild_id] = {
                "delete": 0,
                "edit": 0,
                "total_messages": 0,
            }

    @snipe_metrics_sync.before_loop
    async def before_snipe_metrics_sync(self) -> None:
        await self.bot.wait_until_ready()

    @tasks.loop(hours=24)
    async def snipe_retention_purge(self) -> None:
        """Apply guild retention policies to stored snipes and metrics."""

        now = discord.utils.utcnow()
        for guild_id, policy in self.bot.snipe_retention_settings.items():
            days = policy.get("retention_days", 30)
            days = max(1, days)
            cutoff = now - datetime.timedelta(days=days)
            await self.bot.db.execute(
                "DELETE FROM snipe_delete WHERE guild_id = $1 AND d_m_ts < $2",
                guild_id,
                cutoff,
            )
            await self.bot.db.execute(
                "DELETE FROM snipe_edit WHERE guild_id = $1 AND post_ts < $2",
                guild_id,
                cutoff,
            )
            await self.bot.db.execute(
                "DELETE FROM snipe_metrics WHERE guild_id = $1 AND captured_on < $2",
                guild_id,
                cutoff.date(),
            )

    @snipe_retention_purge.before_loop
    async def before_snipe_retention_purge(self) -> None:
        await self.bot.wait_until_ready()

    def return_ext(self, file: discord.File) -> str:
        filename, ext = os.path.splitext(file.filename)
        return ext.lower()[1:] if ext else ""

    def colorize(self, value: int, thresholds: Dict[int, int]) -> str:
        for threshold, color in thresholds.items():
            if value <= threshold:
                return f"{escape}[0;1;{color}m{value} ms{escape}[0m"

    def get_retention_policy(self, guild_id: int) -> Dict[str, Any]:
        policy = self.bot.snipe_retention_settings.get(guild_id)
        if policy is None:
            return self._default_retention.copy()
        return policy

    def analytics_enabled(self, guild_id: int) -> bool:
        policy = self.get_retention_policy(guild_id)
        return not policy.get("analytics_opt_out", False)

    def format_channel(self, guild: discord.Guild, channel_id: int) -> str:
        channel = guild.get_channel(channel_id)
        if channel is None:
            return f"<#{channel_id}>"
        return channel.mention

    async def build_snipe_analytics_embed(
        self, ctx: BaseContext, window_days: int, max_window: int
    ) -> BaseEmbed:
        window_days = max(1, min(window_days, max_window))
        since_dt = discord.utils.utcnow() - datetime.timedelta(days=window_days)
        metrics_rows = await self.bot.db.fetch(
            """
            SELECT total_messages, delete_count, edit_count
            FROM snipe_metrics
            WHERE guild_id = $1 AND captured_on >= $2
            """,
            ctx.guild.id,
            since_dt.date(),
        )

        totals = {"total_messages": 0, "delete": 0, "edit": 0}
        for row in metrics_rows:
            totals["total_messages"] += row["total_messages"]
            totals["delete"] += row["delete_count"]
            totals["edit"] += row["edit_count"]

        live_counter = self.bot.snipe_counter.get(
            ctx.guild.id, {"total_messages": 0, "delete": 0, "edit": 0}
        )
        totals["total_messages"] += live_counter.get("total_messages", 0)
        totals["delete"] += live_counter.get("delete", 0)
        totals["edit"] += live_counter.get("edit", 0)

        delete_channel_rows = await self.bot.db.fetch(
            """
            SELECT d_m_c_id, COUNT(*) AS count
            FROM snipe_delete
            WHERE guild_id = $1 AND d_m_ts >= $2
            GROUP BY d_m_c_id
            """,
            ctx.guild.id,
            since_dt,
        )
        edit_channel_rows = await self.bot.db.fetch(
            """
            SELECT pre_c_id, COUNT(*) AS count
            FROM snipe_edit
            WHERE guild_id = $1 AND post_ts >= $2
            GROUP BY pre_c_id
            """,
            ctx.guild.id,
            since_dt,
        )

        delete_channel_counter = Counter()
        edit_channel_counter = Counter()

        for row in delete_channel_rows:
            delete_channel_counter[row["d_m_c_id"]] += row["count"]

        for row in edit_channel_rows:
            edit_channel_counter[row["pre_c_id"]] += row["count"]

        attachment_counter = Counter()
        try:
            delete_attachment_rows = await self.bot.db.fetch(
                "SELECT attachment_exts FROM snipe_delete WHERE guild_id = $1 AND d_m_ts >= $2",
                ctx.guild.id,
                since_dt,
            )
            for row in delete_attachment_rows:
                for ext in row["attachment_exts"] or []:
                    attachment_counter[(ext or "unknown").lower()] += 1
        except Exception:
            delete_attachment_rows = await self.bot.db.fetch(
                "SELECT * FROM snipe_delete WHERE guild_id = $1 AND d_m_ts >= $2",
                ctx.guild.id,
                since_dt,
            )
            for row in delete_attachment_rows:
                ext_list = row[9] if len(row) > 9 else []
                for ext in ext_list or []:
                    attachment_counter[(ext or "unknown").lower()] += 1

        try:
            edit_attachment_rows = await self.bot.db.fetch(
                "SELECT pre_attachment_exts FROM snipe_edit WHERE guild_id = $1 AND post_ts >= $2",
                ctx.guild.id,
                since_dt,
            )
            for row in edit_attachment_rows:
                for ext in row["pre_attachment_exts"] or []:
                    attachment_counter[(ext or "unknown").lower()] += 1
        except Exception:
            edit_attachment_rows = await self.bot.db.fetch(
                "SELECT * FROM snipe_edit WHERE guild_id = $1 AND post_ts >= $2",
                ctx.guild.id,
                since_dt,
            )
            for row in edit_attachment_rows:
                ext_list = row[8] if len(row) > 8 else []
                for ext in ext_list or []:
                    attachment_counter[(ext or "unknown").lower()] += 1

        total_actions = totals["delete"] + totals["edit"]
        if total_actions:
            delete_pct = (totals["delete"] / total_actions) * 100
            edit_pct = (totals["edit"] / total_actions) * 100
        else:
            delete_pct = edit_pct = 0.0

        volume_value = textwrap.dedent(
            f"""
            Deleted: `{totals['delete']}` ({delete_pct:.1f}% of actions)
            Edited: `{totals['edit']}` ({edit_pct:.1f}% of actions)
            Total messages tracked: `{totals['total_messages']}`
            """
        )

        channel_lines: List[str] = []
        if delete_channel_counter:
            channel_lines.append("**Deleted**")
            for channel_id, count in delete_channel_counter.most_common(3):
                channel_lines.append(f"{self.format_channel(ctx.guild, channel_id)} — {count}")
        if edit_channel_counter:
            channel_lines.append("**Edited**")
            for channel_id, count in edit_channel_counter.most_common(3):
                channel_lines.append(f"{self.format_channel(ctx.guild, channel_id)} — {count}")
        if not channel_lines:
            channel_lines.append("No channel activity recorded.")

        attachment_lines: List[str] = []
        for ext, count in attachment_counter.most_common(5):
            label = ext.upper() if ext not in {"", "unknown"} else "Unknown"
            attachment_lines.append(f"`{label}` — {count}")
        if not attachment_lines:
            attachment_lines.append("No attachments captured.")

        embed = BaseEmbed(
            title=f"Snipe analytics — last {window_days} day{'s' if window_days != 1 else ''}",
            colour=self.bot.colour,
        )
        embed.add_field(name="Volume", value=volume_value, inline=False)
        embed.add_field(
            name="Top channels",
            value="\n".join(channel_lines),
            inline=False,
        )
        embed.add_field(
            name="Attachment types",
            value="\n".join(attachment_lines),
            inline=False,
        )
        embed.set_footer(
            text=f"Retention window maximum: {max_window} day{'s' if max_window != 1 else ''}"
        )
        return embed

    async def cog_load(self) -> None:
        self.snipe_metrics_sync.start()
        self.snipe_retention_purge.start()

    async def cog_unload(self) -> None:
        self.snipe_metrics_sync.cancel()
        self.snipe_retention_purge.cancel()

    # Listeners for "snipe" command
    @commands.Cog.listener("on_message")
    async def on_message(self, message: discord.Message):
        if message.guild is not None:
            try:
                log = self.bot.settings[message.guild.id]["snipe"]
            except KeyError:
                log = await self.bot.db.fetch(
                    "SELECT snipe FROM guild_settings WHERE guild_id = $1",
                    message.guild.id,
                )
            if log == True and self.analytics_enabled(message.guild.id):
                if message.guild.id not in self.bot.snipe_counter:
                    self.bot.snipe_counter[message.guild.id] = {  # type: ignore
                        "delete": 0,
                        "edit": 0,
                        "total_messages": 0,
                    }
                self.bot.snipe_counter[message.guild.id]["total_messages"] += 1

    @commands.Cog.listener("on_message_delete")
    async def on_message_delete(self, message: discord.Message):
        if message.guild is None:
            return
        try:
            try:
                log = self.bot.settings[message.guild.id]["snipe"]
            except KeyError:
                log = await self.bot.db.fetch(
                    "SELECT snipe FROM guild_settings WHERE guild_id = $1",
                    message.guild.id,
                )

                if isinstance(log, list) and log:
                    log = log[0]["snipe"]

            if log is True:
                if message.author.bot:
                    return

                policy = self.get_retention_policy(message.guild.id)
                anonymize = policy.get("anonymize_attachments", False)
                attachment_opt_out = policy.get("attachment_opt_out", False)

                embeds = []
                attachment_exts: List[str] = []
                attachment_urls: List[str] = []
                attachment_names: List[str] = []
                attachment_bytes: List[bytes] = []

                if message.attachments and not attachment_opt_out:
                    for index, file in enumerate(message.attachments, start=1):
                        try:
                            ext = self.return_ext(file)
                            file_bytes = await file.read()
                            if ext in self.pic_exts:
                                ext = imghdr.what(BytesIO(file_bytes))
                            display_name = file.filename
                            if anonymize:
                                suffix = f".{ext}" if ext else ""
                                display_name = f"attachment-{index}{suffix}"
                            attachment_exts.append(ext or "unknown")
                            attachment_names.append(display_name)
                            attachment_bytes.append(file_bytes)
                        except Exception as e:
                            print(e)

                if attachment_names and not attachment_opt_out and len(attachment_names) >= 2:
                    attachment_bytes.clear()
                    try:
                        for index, attachment in enumerate(
                            message.attachments, start=1
                        ):
                            async with aiohttp.ClientSession() as session:
                                wbhk = discord.Webhook.partial(
                                    id=self.bot.config.get("SNIPE_ATTACHMENT_ID"),
                                    token=self.bot.config.get("SNIPE_ATTACHMENT_TOKEN"),
                                    session=session,
                                )
                                _attachment = await attachment.read()
                                sent_attachment_message = await wbhk.send(
                                    file=discord.File(
                                        BytesIO(_attachment),
                                        filename=attachment.filename,
                                    ),
                                    wait=True,
                                )
                                attachment_urls.append(
                                    sent_attachment_message.attachments[0].url
                                )
                    except Exception as e:
                        print(f"Error with webhook for attachments: {e}")

                # Process embeds
                if message.embeds:
                    for embed in message.embeds:
                        embeds.append(embed.to_dict())

                # Insert into database
                try:
                    query = """
                    INSERT INTO snipe_delete
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """

                    await self.bot.db.execute(
                        query,
                        message.guild.id,
                        message.channel.id,
                        message.author.id,
                        message.content,
                        message.created_at,
                        embeds,
                        attachment_names,
                        attachment_bytes,
                        attachment_urls,
                        attachment_exts,
                    )

                    # Update counter
                    if self.analytics_enabled(message.guild.id):
                        try:
                            self.bot.snipe_counter[message.guild.id]["delete"] += 1
                        except KeyError:
                            # Initialize counter if it doesn't exist
                            if message.guild.id not in self.bot.snipe_counter:
                                self.bot.snipe_counter[message.guild.id] = {
                                    "delete": 1,
                                    "edit": 0,
                                    "total_messages": 0,
                                }
                            else:
                                self.bot.snipe_counter[message.guild.id]["delete"] = 1

                except Exception as e:
                    print(f"Error inserting into snipe_delete: {e}")

        except Exception as e:
            print(f"Error in on_message_delete: {e}")

    @commands.Cog.listener("on_message_edit")
    async def on_message_edit(self, pre: discord.Message, post: discord.Message):
        if pre.guild is not None:
            try:
                log = self.bot.settings[pre.guild.id]["snipe"]
            except KeyError:
                log = await self.bot.db.fetch(
                    "SELECT snipe FROM guild_settings WHERE guild_id = $1",
                    pre.guild.id,
                )

            if log == True:
                if pre.author.bot and post.author.bot:
                    return
                policy = self.get_retention_policy(pre.guild.id)
                anonymize = policy.get("anonymize_attachments", False)
                attachment_opt_out = policy.get("attachment_opt_out", False)
                pre_attachment_exts: List[str] = []
                pre_attachment_urls: List[str] = []
                pre_attachment_names: List[str] = []
                pre_attachment_bytes: List[bytes] = []

                post_attachment_exts: List[str] = []
                post_attachment_urls: List[str] = []
                post_attachment_names: List[str] = []
                post_attachment_bytes: List[bytes] = []

                if pre.attachments and not attachment_opt_out:
                    for index, file in enumerate(pre.attachments, start=1):
                        ext = self.return_ext(file)
                        file_bytes = await file.read()
                        if ext in self.pic_exts:
                            ext = imghdr.what(BytesIO(file_bytes))
                        name = file.filename
                        if anonymize:
                            suffix = f".{ext}" if ext else ""
                            name = f"attachment-pre-{index}{suffix}"
                        pre_attachment_exts.append(ext or "unknown")
                        pre_attachment_names.append(name)
                        pre_attachment_bytes.append(file_bytes)

                if pre_attachment_names and not attachment_opt_out and len(pre_attachment_names) >= 2:
                    pre_attachment_bytes.clear()
                    for attachment in pre.attachments:
                        async with aiohttp.ClientSession() as session:
                            wbhk = discord.Webhook.partial(
                                id=self.bot.config.get("SNIPE_ATTACHMENT_ID"),
                                token=self.bot.config.get("SNIPE_ATTACHMENT_TOKEN"),
                                session=session,
                            )

                            _attachment = await attachment.read()
                            sent_attachment_message = await wbhk.send(
                                file=discord.File(
                                    BytesIO(_attachment), filename=attachment.filename
                                ),
                                wait=True,
                            )
                            pre_attachment_urls.append(
                                sent_attachment_message.attachments[0].url
                            )

                if post.attachments and not attachment_opt_out:
                    for index, _file in enumerate(post.attachments, start=1):
                        ext = self.return_ext(_file)
                        file_bytes = await _file.read()
                        if ext in self.pic_exts:
                            ext = imghdr.what(BytesIO(file_bytes))
                        name = _file.filename
                        if anonymize:
                            suffix = f".{ext}" if ext else ""
                            name = f"attachment-post-{index}{suffix}"
                        post_attachment_exts.append(ext or "unknown")
                        post_attachment_names.append(name)
                        post_attachment_bytes.append(file_bytes)

                if post_attachment_names and not attachment_opt_out and len(post_attachment_names) >= 2:
                    post_attachment_bytes.clear()
                    for _attachment in post.attachments:
                        async with aiohttp.ClientSession() as session:
                            wbhk = discord.Webhook.partial(
                                id=self.bot.config.get("SNIPE_ATTACHMENT_ID"),
                                token=self.bot.config.get("SNIPE_ATTACHMENT_TOKEN"),
                                session=session,
                            )

                            __attachment = await _attachment.read()
                            _sent_attachment_message = await wbhk.send(
                                file=discord.File(
                                    BytesIO(__attachment), filename=_attachment.filename
                                ),
                                wait=True,
                            )
                            post_attachment_urls.append(
                                _sent_attachment_message.attachments[0].url
                            )

                query: str = """
                INSERT INTO snipe_edit
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)"""

                await self.bot.db.execute(
                    query,
                    pre.guild.id,
                    pre.channel.id,
                    pre.id,
                    pre.author.id,
                    pre.content,
                    pre.created_at,
                    post.content,
                    post.created_at,
                    pre_attachment_exts,
                    pre_attachment_urls,
                    pre_attachment_names,
                    pre_attachment_bytes,
                    post_attachment_names,
                    post_attachment_urls,
                    post_attachment_names,
                    post_attachment_bytes,
                    post.jump_url,
                )
                if self.analytics_enabled(post.guild.id):
                    try:
                        self.bot.snipe_counter[post.guild.id]["edit"] += 1
                    except KeyError:
                        self.bot.snipe_counter[post.guild.id] = {
                            "delete": 0,
                            "edit": 1,
                            "total_messages": 0,
                        }

    @commands.hybrid_command(name="ping", brief="You ping Me", aliases=["pong"])
    @app_commands.checks.cooldown(2, 10)
    @commands.cooldown(2, 10, commands.BucketType.user)
    async def ping(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Get proper latency timings of the bot."""

        # Latency for typing
        typing_start = time.perf_counter()
        async with ctx.typing():
            await asyncio.sleep(0.5)
        typing_end = time.perf_counter()
        typing_ping = (typing_end - typing_start) * 1000
        typing_ping = round(typing_ping, 1)

        # Latency with the database
        start_db = time.perf_counter()
        await self.bot.db.fetch("SELECT 1")
        end_db = time.perf_counter()
        db_ping = round((end_db - start_db) * 1000, 1)

        # Latency for Discord Api
        websocket_ping = round(self.bot.latency * 1000, 0)

        mob_type_ping = typing_ping
        mob_db_ping = db_ping
        mob_wb_ping = websocket_ping

        typing_threshold: Dict[int, int] = {900: 32, 1000: 33, 1500: 31}

        db_thresholds: Dict[int, int] = {5: 32, 15: 33, 20: 31}

        websocket_thresholds: Dict[int, int] = {
            350: 32,
            450: 33,
            500: 31,
        }
        typing_ping = self.colorize(typing_ping, typing_threshold)
        db_ping = self.colorize(db_ping, db_thresholds)
        websocket_ping = self.colorize(websocket_ping, websocket_thresholds)

        ping_emb = BaseEmbed(title="__ My Latencies : __", colour=0x2F3136)

        if ctx.interaction:
            if ctx.author.is_on_mobile():
                ping_emb.description = f"""```yaml\n> PostgreSQL     : {mob_db_ping}
> Discord API    : {mob_wb_ping}\n```"""
                return await ctx.reply(
                    embed=ping_emb, mention_author=False, ephemeral=True
                )
            else:
                ping_emb.description = f"""```ansi\n{escape}[0;1;37;40m > {escape}[0m {escape}[0;1;34mPostgreSQL{escape}[0m     {escape}[0;1;37;40m : {escape}[0m {db_ping}{escape}[0m
{escape}[0;1;37;40m > {escape}[0m {escape}[0;1;34mDiscord API{escape}[0m    {escape}[0;1;37;40m : {escape}[0m {escape}[0;1;31m{websocket_ping} {escape}[0m\n```"""
                return await ctx.reply(
                    embed=ping_emb, mention_author=False, ephemeral=True
                )
        else:
            if ctx.author.is_on_mobile():
                ping_emb.description = f"""```yaml\n> PostgreSQL     : {mob_db_ping} ms
> Discord API    : {mob_wb_ping} ms
> Message Typing : {mob_type_ping} ms\n```"""
                return await ctx.reply(embed=ping_emb, mention_author=False)
            else:
                ping_emb.description = f"""```ansi\n{escape}[0;1;37;40m > {escape}[0m {escape}[0;1;34mPostgreSQL{escape}[0m     {escape}[0;1;37;40m : {escape}[0m {escape}[0;1;31m{db_ping}{escape}[0m
{escape}[0;1;37;40m > {escape}[0m {escape}[0;1;34mDiscord API{escape}[0m    {escape}[0;1;37;40m : {escape}[0m {escape}[0;1;31m{websocket_ping}{escape}[0m
{escape}[0;1;37;40m > {escape}[0m {escape}[0;1;34mMessage Typing{escape}[0m {escape}[0;1;37;40m : {escape}[0m {escape}[0;1;31m{typing_ping}{escape}[0m\n```"""
            return await ctx.reply(embed=ping_emb, mention_author=False)

    @commands.command(name="banner", brief="View a persons banner")
    async def banner(
        self, ctx: BaseContext, *, user: Union[discord.Member, discord.User] = None
    ) -> Optional[discord.Message]:
        """See the user's Banner in an enlarged manner."""
        user = user or ctx.author
        if ctx.message.reference:
            user = ctx.message.reference.resolved.author
        fetched_user = await ctx.bot.fetch_user(user.id)
        if fetched_user.banner is None:
            return await ctx.reply(
                f"**{user}** does not have a banner <a:Grimacing:914905757588283422>"
            )
        banner_emb = BaseEmbed(
            title=f"{user}'s Banner",
            colour=user.colour or user.accent_color or self.bot.colour,
        )
        banner_emb.set_image(url=fetched_user.banner.url)
        await ctx.reply(embed=banner_emb, mention_author=False)

    # Get user's PFP
    @commands.command(
        name="avatar", brief="View a persons PFP", aliases=["pfp", "pp", "dp", "av"]
    )
    async def avatar(
        self, ctx: BaseContext, *, user: Union[discord.User, discord.Member] = None
    ) -> Optional[discord.Message]:
        """See the user's PFP in an enlarged manner."""
        user = user or ctx.author
        if ctx.message.reference:
            user = ctx.message.reference.resolved.author
            return await PFP(self.bot, ctx, user).send()
        if user == ctx.author:
            log_avatar = await self.bot.db.fetchval(
                "SELECT avatar FROM user_settings WHERE user_id = $1", ctx.author.id
            )
            if not log_avatar:
                no_avatar_log_user = PFP(self.bot, ctx, ctx.author)
                no_avatar_log_user.save.disabled = True
                return await no_avatar_log_user.send()
            if log_avatar:
                avatar_log_user = PFP(self.bot, ctx, ctx.author)
                return await avatar_log_user.send()
        await PFP(self.bot, ctx, user).send()

    # Get user's information
    @commands.hybrid_command(
        name="userinfo",
        brief="Get user information",
        aliases=["user", "ui"],
        with_app_command=True,
    )
    @commands.guild_only()
    async def userinfo(
        self, ctx: BaseContext, *, user: discord.Member = None
    ) -> Optional[discord.Message]:
        """Get entire details about a user."""
        user = user or ctx.author
        if ctx.message.reference:
            user = ctx.message.reference.resolved.author
        roles = ""
        for role in user.roles:
            if role is ctx.guild.default_role:
                continue
            roles = f"{roles} {role.mention}"
        if roles != "":
            roles = f"{roles}"
        fetched_user = await ctx.bot.fetch_user(user.id)
        permissions = user_perms(user.guild_permissions)
        perms_: None = "None"
        if permissions:
            perms_ = f"{' **|** '}".join(permissions)
        avatar = user.display_avatar.with_static_format("png")
        status = str(user.status).capitalize()
        colour: discord.colour.Colour = user.colour
        if colour == discord.Colour.from_rgb(0, 0, 0):
            colour = 0x2F3136

        general_emb = BaseEmbed(title=f":scroll: {user}'s Information", colour=colour)
        general_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> General Info :",
            value=f"> <:ReplyContinued:930634770004725821> Name: {user.mention} \n"
            f"> <:ReplyContinued:930634770004725821> Nickname: {(user.nick) or 'No nickname set'} \n"
            # f"> <:ReplyContinued:930634770004725821> Discriminator: `#{user.discriminator}` \n" No discriminators
            f"> <:Reply:930634822865547294> Identification No.: `{user.id}` \n────",
        )
        general_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Account Info:",
            value=f"> <:ReplyContinued:930634770004725821> Join Position: `#{sorted(ctx.guild.members, key = lambda u: u.joined_at or discord.utils.utcnow()).index(user) + 1}`\n "
            f"> <:ReplyContinued:930634770004725821> Created on: {self.bot.timestamp(user.created_at, style = 'd')} ({self.bot.timestamp(user.created_at, style = 'R')}) \n"
            f"> <:Reply:930634822865547294> Joined Guild on: {self.bot.timestamp(user.joined_at, style = 'd')} ({self.bot.timestamp(user.joined_at, style = 'R')})\n────",
            inline=False,
        )
        general_emb.set_thumbnail(url=avatar)

        guild_emb = BaseEmbed(title=f":scroll: {user} in {ctx.guild}", colour=colour)
        guild_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Permissions Present:",
            value=f"> <:Reply:930634822865547294> {perms_}\n────",
        )
        guild_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Top Most Role:",
            value=f"> <:Reply:930634822865547294> {user.top_role.mention}\n────",
            inline=False,
        )
        guild_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> All Roles Present:",
            value=f"> <:Reply:930634822865547294> {roles}\n────",
            inline=False,
        )
        guild_emb.set_thumbnail(url=avatar)

        misc_emb = BaseEmbed(
            title=f":scroll: {user}'s - Misc. Information", colour=colour
        )
        misc_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Badges Present:",
            value=f"> <:Reply:930634822865547294> {user_badges(user=user) if user_badges(user=user) else 'No Badges Present'}",
        )
        misc_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Accent Colours:",
            value=f"> <:ReplyContinued:930634770004725821> Banner Colour: `{str(fetched_user.accent_colour).upper()}` \n"
            f"> <:Reply:930634822865547294> Guild Role Colour: `{user.color if user.color is not discord.Color.default() else 'Default'}`\n────",
            inline=False,
        )
        misc_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Custom Status:",
            value=f"> <:Reply:930634822865547294> {status}",
            inline=False,
        )
        misc_emb.set_thumbnail(url=avatar)

        pfp_emb = BaseEmbed(
            title=f":scroll: {user}'s PFP",
            description=f"[**JPG Format**]({user.display_avatar.with_static_format('jpg')}) │ [**PNG Format**]({user.display_avatar.with_static_format('png')}) │ [**WEBP Format**]({user.display_avatar.with_static_format('webp')})",
            colour=colour,
        )
        pfp_emb.set_image(url=avatar)

        banner_emb = None

        if fetched_user.banner is None:
            embed_list = [general_emb, guild_emb, misc_emb, pfp_emb]
            async with ctx.channel.typing():
                await asyncio.sleep(0.1)
            await Paginator(self.bot, ctx, embeds=embed_list).send(ctx)
        else:
            banner_emb = BaseEmbed(
                title=f":scroll: {user}'s Banner",
                description=f"[**Download Banner Here**]({fetched_user.banner.url})",
                colour=colour,
            )
            banner_emb.set_image(url=fetched_user.banner.url)

            embed_list = [general_emb, guild_emb, misc_emb, pfp_emb, banner_emb]
            async with ctx.channel.typing():
                await asyncio.sleep(0.1)
            await Paginator(self.bot, ctx, embeds=embed_list).send(ctx)

    @commands.hybrid_command(
        name="serverinfo",
        brief="Get guild information",
        aliases=["si", "gi"],
        with_app_command=True,
    )
    @commands.guild_only()
    async def server_info(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Get entire details about the guild."""
        user_status = [
            len(list(filter(lambda u: str(u.status) == "online", ctx.guild.members))),
            len(list(filter(lambda u: str(u.status) == "idle", ctx.guild.members))),
            len(list(filter(lambda u: str(u.status) == "dnd", ctx.guild.members))),
            len(list(filter(lambda u: str(u.status) == "offline", ctx.guild.members))),
        ]
        fetched_guild = await ctx.bot.fetch_guild(ctx.guild.id)

        general_emb = BaseEmbed(
            title=f":scroll: {ctx.guild.name}'s Information", colour=self.bot.colour
        )
        general_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> General Information :",
            value=f"> <:ReplyContinued:930634770004725821> <a:WumpusHypesquad:905661121501990923> Owner: {ctx.guild.owner.mention} (`{ctx.guild.owner.id}`) \n"
            f"> <:ReplyContinued:930634770004725821> <a:Users:905749451350638652> No. of Roles: `{len(ctx.guild.roles)}` \n"
            f"> <:ReplyContinued:930634770004725821> <a:Info:905750331789561856> Identification No.: `{ctx.guild.id}` \n"
            f"> <:ReplyContinued:930634770004725821> <a:Verify:905748402871095336> Verification Level: {str(ctx.guild.verification_level).replace('_', ' ').replace('`NONE`', '`NILL`').title()} \n"
            f"> <:Reply:930634822865547294> <:WinFileBruh:898571301986373692> File Transfer Limit: `{humanize.naturalsize(ctx.guild.filesize_limit)}`\n────",
        )
        general_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Initialisation :",
            value=f"> <:ReplyContinued:930634770004725821> <a:Woo:905754435379163176> Made On: {self.bot.timestamp(ctx.guild.created_at, style='d')} \n"
            f"> <:Reply:930634822865547294> <:ISus:915817563307515924> Media Filteration: For `{str(ctx.guild.explicit_content_filter).replace('_',' ').replace('`NONE`', '`NILL`').title()}` \n────",
            inline=False,
        )
        general_emb.set_thumbnail(url=ctx.guild.icon.url)

        other_emb = BaseEmbed(
            title=f":scroll: {ctx.guild.name}'s Other Information",
            colour=self.bot.colour,
        )
        other_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Channel Information:",
            value=f"> <:ReplyContinued:930634770004725821> <:Channel:905674680436944906> Text: `{len(ctx.guild.text_channels)}` \n"
            f"> <:ReplyContinued:930634770004725821> <:Voice:905746719034187796> Voice: `{len(ctx.guild.voice_channels)}` \n"
            f"> <:ReplyContinued:930634770004725821> <a:Thread:905750997706629130> Threads: `{len(ctx.guild.threads)}` \n"
            f"> <:Reply:930634822865547294> <:StageChannel:905674422839554108> Stage: `{len(ctx.guild.stage_channels)}` \n────",
            inline=False,
        )
        other_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Emotes Present:",
            value=f"> <:ReplyContinued:930634770004725821> <a:IThink:933315875501641739> Animated: `{len([animated for animated in ctx.guild.emojis if animated.animated])}` / `{ctx.guild.emoji_limit}` \n"
            f"> <:Reply:930634822865547294> <:BallManHmm:933398958263386222> Non - Animated: `{len([non_animated for non_animated in ctx.guild.emojis if not non_animated.animated])}` / `{ctx.guild.emoji_limit}`\n────",
            inline=False,
        )
        other_emb.set_thumbnail(url=ctx.guild.icon.url)

        user_emb = BaseEmbed(
            title=f":scroll: {ctx.guild.name}'s Users Information",
            colour=self.bot.colour,
        )
        user_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> No. of Users:",
            value=f"> <:ReplyContinued:930634770004725821> <a:HumanBro:905748764432662549> No. of Humans: `{len(list(filter(lambda u : u.bot is False, ctx.guild.members)))}` \n"
            f"> <:ReplyContinued:930634770004725821> <a:BotLurk:905749164355379241> No. of Bots: `{len(list(filter(lambda u : u.bot, ctx.guild.members)))}` \n"
            f"> <:Reply:930634822865547294> <a:Users:905749451350638652> Total: `{ctx.guild.member_count}`\n────",
            inline=False,
        )
        user_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Activity Information:",
            value=f"> <:ReplyContinued:930634770004725821> <:Online:905757053119766528> Online: `{user_status[0]}` \n"
            f"> <:ReplyContinued:930634770004725821> <:Idle:905757063064453130> Idle: `{user_status[1]}` \n"
            f"> <:ReplyContinued:930634770004725821> <:DnD:905759353141874709> Do Not Disturb: `{user_status[2]}` \n"
            f"> <:Reply:930634822865547294> <:Offline:905757032521551892> Offline: `{user_status[3]}`\n────",
            inline=False,
        )
        user_emb.set_thumbnail(url=ctx.guild.icon.url)

        icon_emb = BaseEmbed(
            title=f":scroll: {ctx.guild.name}'s Icon",
            description=f"[**JPG Format**]({ctx.guild.icon.with_static_format('jpg')}) │ [**PNG Format**]({ctx.guild.icon.with_static_format('png')}) │ [**WEBP Format**]({ctx.guild.icon.with_static_format ('webp')})",
            colour=self.bot.colour,
        )
        icon_emb.set_image(url=ctx.guild.icon.url)

        banner_emb = None

        if fetched_guild.banner is None:
            embed_list = [general_emb, other_emb, user_emb, icon_emb]
            async with ctx.channel.typing():
                await asyncio.sleep(0.1)
            await Paginator(self.bot, ctx, embeds=embed_list).send(ctx)
        else:
            banner_emb = BaseEmbed(
                title=f":scroll: {ctx.guild.name}'s Banner",
                description=f"[**Download Banner Here**]({fetched_guild.banner.url})",
                colour=self.bot.colour,
            )
            banner_emb.set_image(url=fetched_guild.banner.url)

            embed_list = [general_emb, other_emb, user_emb, icon_emb, banner_emb]
            async with ctx.channel.typing():
                await asyncio.sleep(0.1)
            await Paginator(self.bot, ctx, embeds=embed_list).send(ctx)

    @commands.command(name="spotify", brief="Get Spotify Info.", aliases=["sp", "spot"])
    async def spotify(
        self, ctx: BaseContext, *, user: Union[discord.Member, discord.User] = None
    ) -> Optional[discord.Message]:
        """Get Information on what the user is listening to."""
        user = user or ctx.author
        view = discord.ui.View()
        try:
            spotify = discord.utils.find(
                lambda sp: isinstance(sp, discord.Spotify), user.activities
            )
        except BaseException:
            return await ctx.reply(f"`{user}` is not in this guild, I'm sorry.")
        if spotify is None:
            if user == ctx.author:
                return await ctx.reply("You are not listening to Spotify right now.")
            else:
                return await ctx.reply(
                    f"**{user}** is not listening to any song on **Spotify** right now."
                )
        else:
            spotify_emb = BaseEmbed(
                title=f":scroll: {user}'s Spotify Status",
                description=f"They are listening to [**{spotify.title}**]({spotify.track_url}) by - **{spotify.artist}**",
                colour=self.bot.colour,
            )
            spotify_emb.add_field(
                name="Song Information :",
                value=f"> <:ReplyContinued:930634770004725821> ` - ` **Name :** [**{spotify.title}**]({spotify.track_url})\n"
                f"> <:ReplyContinued:930634770004725821> ` - ` **Album :** {spotify.album}\n"
                f"> <:Reply:930634822865547294> ` - ` **Duration :** {humanize.precisedelta(spotify.duration)}",
            )
            spotify_emb.set_thumbnail(url=spotify.album_cover_url)
            view.add_item(
                discord.ui.Button(
                    label="Listen on Spotify",
                    url=spotify.track_url,
                    emoji="<a:Spotify:993120872883834990>",
                )
            )
            await ctx.reply(embed=spotify_emb, mention_author=False, view=view)

    # Snipe command as a group
    # TODO: Finish :meth: ~ snipe_edit(). Too lazy
    @commands.hybrid_group(name="snipe", aliases=["s"], with_app_command=True)
    @commands.cooldown(3, 5, commands.BucketType.user)
    @commands.guild_only()
    async def snipe(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Get edited / deleted messages"""
        if ctx.invoked_subcommand is None:
            await ctx.command_help()

    # Snipes for deleted messages
    @snipe.command(
        name="delete",
        brief="Snipe Deleted Messages",
        aliases=["del", "d"],
        with_app_command=True,
    )
    @commands.cooldown(3, 5, commands.BucketType.user)
    @app_commands.describe(
        index="The order at which you want to snipe.",
        channel="The text-channel do you want to snipe.",
        user="Filter sniped messages according to a user.",
    )
    async def snipe_delete(
        self,
        ctx: BaseContext,
        index: Optional[int],
        channel: Optional[discord.TextChannel],
        user: Optional[Union[discord.User, discord.Member]],
    ) -> Optional[discord.Message]:
        """Sends details on recently deleted message."""

        if not index:
            index = 0
        if not channel:
            channel = ctx.channel
        if not user:
            query: str = (
                f"SELECT * FROM snipe_delete WHERE guild_id = $1 AND d_m_c_id = $2 ORDER BY d_m_ts DESC OFFSET {index} LIMIT 1"
            )
            snipe_records = await self.bot.db.fetch(query, ctx.guild.id, channel.id)
        else:
            query: str = (
                f"SELECT * FROM snipe_delete WHERE guild_id = $1 AND d_m_a_id = $2 AND d_m_c_id = $3 ORDER BY d_m_ts DESC OFFSET {index} LIMIT 1"
            )
            snipe_records = await self.bot.db.fetch(
                query, ctx.guild.id, user.id, channel.id
            )
        if not snipe_records:
            return await ctx.send(
                f"**{ctx.guild}** - has no snipes recorded in {channel.mention} <a:IWait:948253556190904371>"
            )

        _embed: BaseEmbed = None

        for record in snipe_records:
            user = ctx.guild.get_member(record[2])
            _time = discord.utils.utcnow() - record[4]

            snipe_embed = BaseEmbed(
                description=record[3] if record[3] else "_No content was present._",
                color=self.bot.colour,
            )
            snipe_embed.set_author(
                name=f"{user} said in {ctx.guild.get_channel(record[1])} ...",
                icon_url=user.display_avatar.url,
            )
            snipe_embed.set_footer(text=f"Deleted {humanize.precisedelta(_time)} ago")

            file = record[7][0] if record[7] else None
            file_urls: List[str] = [url for url in record[8] if record[8] >= 2]
            embeds: List[BaseEmbed] = [snipe_embed]

            if record[5]:
                for _dict in record[5]:
                    embeds.append(BaseEmbed().from_dict(dict(_dict)))

            try:
                for z in record[6]:
                    if z.split(".")[-1] in self.pic_exts:
                        snipe_embed.set_image(url=file_urls[0])
            except IndexError:
                pass

            serial_no: int = 1
            for x in file_urls:
                if x.split(".")[-1] in self.pic_exts:
                    if x == snipe_embed.image.url:
                        continue
                    embed = snipe_embed.copy()
                    embed.set_image(url=x)
                    embeds.append(embed)
                else:
                    snipe_embed.add_field(
                        name="Urls for Attachments",
                        value=f"[Attachment {serial_no}]({x})",
                        inline=False,
                    )
                    serial_no += 1

            if file_urls:
                for gamma in file_urls:
                    if gamma.split(".")[-1] in self.pic_exts:
                        return await Paginator(self.bot, ctx, embeds).send(ctx)
                else:
                    await ctx.send(embed=snipe_embed)
            elif file:
                if index == 0:
                    if len(embeds) == 1:
                        view = SnipeAttachmentViewer(
                            ctx, file_data=file, filename=record[6][0]
                        )
                        view.message = await ctx.send(embeds=embeds, view=view)
                        return
                    view = SnipeAttachmentViewer(
                        ctx, file_data=file, filename=record[6][0]
                    )
                    view.message = await ctx.send(embeds=embeds, view=view)
                else:
                    if len(embeds) == 1:
                        view = SnipeAttachmentViewer(
                            ctx, embeds=embeds, file_data=file, filename=record[6][0]
                        )
                        view.message = await ctx.send(embeds=embeds, view=view)
                        return
                    view = SnipeAttachmentViewer(
                        ctx, file_data=file, filename=record[6][0]
                    )
                    view.message = await ctx.send(embeds=embeds, view=view)
            else:
                if index == 0:
                    if len(embeds) == 1:
                        await ctx.send(embed=snipe_embed)
                    else:
                        await ctx.send(embeds=embeds)
                else:
                    if len(embeds) == 1:
                        await ctx.send(embed=snipe_embed)
                    else:
                        await ctx.send(embeds=embeds)

    # Snipes for edited messages
    @snipe.command(
        name="edit",
        brief="Snipe Edited Messages",
        aliases=["ed", "e"],
        with_app_command=True,
    )
    @commands.cooldown(3, 5, commands.BucketType.user)
    @app_commands.describe(
        channel="The text-channel do you want to snipe.",
        user="Filter sniped messages according to a user.",
        index="The order at which you want to snipe.",
    )
    async def snipe_edit(
        self,
        ctx: BaseContext,
        channel: Optional[discord.TextChannel],
        user: Optional[Union[discord.Member, discord.User]],
        index: Optional[int] = 0,
    ) -> Optional[discord.Message]:
        """Get the details of the recently edited message"""

        if not channel:
            channel = ctx.channel

        if not user:
            query: str = (
                f"SELECT * FROM snipe_edit WHERE guild_id = $1 AND pre_c_id = $2 ORDER BY post_ts DESC OFFSET {index} LIMIT 1"
            )
            snipe_records = await self.bot.db.fetch(query, ctx.guild.id, channel.id)
            if not snipe_records:
                return await ctx.send(
                    f"**{ctx.guild}** - has no snipes recorded in {channel.mention} <a:IWait:948253556190904371>"
                )
        else:
            query: str = (
                f"SELECT * FROM snipe_edit WHERE guild_id = $1 AND pre_c_id = $2 AND pre_m_a_id = $3 ORDER BY post_ts DESC OFFSET {index} LIMIT 1"
            )
            snipe_records = await self.bot.db.fetch(
                query, ctx.guild.id, channel.id, user.id
            )
            if not snipe_records:
                return await ctx.send(
                    f"**{ctx.guild}** - has no snipes recorded in {channel.mention} for {user.mention} <a:IWait:948253556190904371>",
                    allowed_mentions=self.bot.allowed_mentions,
                )

        _embed: BaseEmbed = None

        for record in snipe_records:
            user = ctx.guild.get_member(record[3])
            _time = discord.utils.utcnow() - record[7]

            description: str = f"""
            **Before Edit:**
            {record[4] if record[4] else '_No content was present._'}

            **After Edit:**
            {record[6] if record[6] else '_No content was present._'}"""
            snipe_embed = BaseEmbed(
                description=description,
                colour=self.bot.colour,
            )
            snipe_embed.set_author(
                icon_url=user.display_avatar.url,
                name=f"{user} edited in {ctx.guild.get_channel(record[1])}",
            )
            view = discord.ui.View()
            view.add_item(
                discord.ui.Button(
                    label="Jump Url",
                    style=discord.ButtonStyle.grey,
                    emoji="<a:ChainLink:936158619030941706>",
                    url=record[16],
                )
            )
            snipe_embed.set_footer(text=f"Edited {humanize.precisedelta(_time)}")

            # pre_file_names: List[str] = record[10] or []
            # pre_file_bytes: List[bytes] = record[1] or []

            # post_file_names: List[str] = record[14] or []
            # post_file_bytes: List[bytes] = record[15] or []

            # if record[10]:
            #     for name in record[10]:
            #         pre_file_names.append(name)

            # if post_file_bytes:
            #     view = EditSnipeAttachmentView(
            #         ctx,
            #         pre_file_bytes,
            #         post_file_bytes,
            #     )
            #     view.message = await ctx.send(embed=snipe_embed,view=view)
            #     return

        await ctx.send(embed=snipe_embed, view=view)

    @snipe.command(name="stats", brief="Stats on snipe", with_app_command=True)
    async def snipe_stats(self, ctx: BaseContext, flag: Optional[SnipeStats]):
        """Get guild and global snipe stats
        ────
        **Flags Present:**
        `--globalstats`: Sends global stats for snipe.
        <:Join:932976724235395072> **Arg Needed**: `True` or `False`
        **Example:**
        `.gsnipe stats [--globalstats True]`
        """
        uptime_window = discord.utils.utcnow() - self.bot.uptime

        if flag and flag.globalstats:
            row = await self.bot.db.fetchrow(
                """
                SELECT
                    COALESCE(SUM(total_messages), 0) AS total_messages,
                    COALESCE(SUM(delete_count), 0) AS delete_count,
                    COALESCE(SUM(edit_count), 0) AS edit_count
                FROM snipe_metrics
                """
            )
            totals = {
                "total_messages": row["total_messages"] if row else 0,
                "delete": row["delete_count"] if row else 0,
                "edit": row["edit_count"] if row else 0,
            }
            for guild_id, counter in self.bot.snipe_counter.items():
                if not self.analytics_enabled(guild_id):
                    continue
                totals["total_messages"] += counter.get("total_messages", 0)
                totals["delete"] += counter.get("delete", 0)
                totals["edit"] += counter.get("edit", 0)

            description = textwrap.dedent(
                f"""
                **Global analytics**
                <:ReplyContinued:930634770004725821> **Deleted:** `{totals['delete']}`
                <:ReplyContinued:930634770004725821> **Edited:** `{totals['edit']}`
                <:Reply:930634822865547294> **Total Messages:** `{totals['total_messages']}`
                """
            )
            embed = BaseEmbed(
                title="Global snipe statistics",
                description=description,
                colour=self.bot.colour,
            )
            embed.set_footer(text="Includes all guilds with analytics enabled")
            return await ctx.send(embed=embed)

        policy = self.get_retention_policy(ctx.guild.id)
        window_days = min(policy.get("retention_days", 30), 90)
        since = discord.utils.utcnow().date() - datetime.timedelta(days=window_days - 1)
        rows = await self.bot.db.fetch(
            """
            SELECT total_messages, delete_count, edit_count
            FROM snipe_metrics
            WHERE guild_id = $1 AND captured_on >= $2
            """,
            ctx.guild.id,
            since,
        )

        totals = {"total_messages": 0, "delete": 0, "edit": 0}
        for row in rows:
            totals["total_messages"] += row["total_messages"]
            totals["delete"] += row["delete_count"]
            totals["edit"] += row["edit_count"]

        counter = self.bot.snipe_counter.get(
            ctx.guild.id, {"total_messages": 0, "delete": 0, "edit": 0}
        )
        totals["total_messages"] += counter.get("total_messages", 0)
        totals["delete"] += counter.get("delete", 0)
        totals["edit"] += counter.get("edit", 0)

        description = textwrap.dedent(
            f"""
            Window: last {window_days} day{'s' if window_days != 1 else ''}
            <:ReplyContinued:930634770004725821> **Deleted:** `{totals['delete']}`
            <:ReplyContinued:930634770004725821> **Edited:** `{totals['edit']}`
            <:Reply:930634822865547294> **Total Messages:** `{totals['total_messages']}`
            ⏱️ Runtime window: {humanize.precisedelta(uptime_window)}
            """
        )
        stats_emb = BaseEmbed(
            title=f"Snipe stats for {ctx.guild}",
            description=description,
            colour=self.bot.colour,
        )
        stats_emb.set_footer(
            icon_url=ctx.author.display_avatar.url, text=f"Invoked by: {ctx.author}"
        )
        return await ctx.send(embed=stats_emb)

    @commands.hybrid_group(
        name="analytics",
        brief="Interactive analytics dashboards",
        with_app_command=True,
    )
    @commands.guild_only()
    async def analytics(self, ctx: BaseContext) -> Optional[discord.Message]:
        if ctx.invoked_subcommand is None:
            return await ctx.command_help()

    @analytics.command(
        name="snipe",
        brief="Show snipe analytics dashboard",
        with_app_command=True,
    )
    @app_commands.describe(days="Number of days to include in the dashboard.")
    async def analytics_snipe(
        self, ctx: BaseContext, days: Optional[app_commands.Range[int, 1, 90]] = None
    ) -> Optional[discord.Message]:
        if ctx.guild is None:
            return None

        if not self.analytics_enabled(ctx.guild.id):
            return await ctx.reply(
                "Snipe analytics are disabled for this guild. Use"
                f" `{ctx.clean_prefix}guild snipe analytics False` to enable data collection.",
                mention_author=False,
            )

        policy = self.get_retention_policy(ctx.guild.id)
        max_window = min(policy.get("retention_days", 30), 90)
        if max_window <= 0:
            max_window = 1

        requested_window = days or min(7, max_window)

        if ctx.interaction and not ctx.interaction.response.is_done():
            await ctx.defer()

        embed = await self.build_snipe_analytics_embed(ctx, requested_window, max_window)

        available_windows = [
            value
            for value in (1, 3, 7, 14, 30, 60, 90)
            if value <= max_window
        ]
        if requested_window not in available_windows:
            available_windows.append(requested_window)
        available_windows = sorted(set(available_windows))

        async def refresh(new_days: int) -> BaseEmbed:
            return await self.build_snipe_analytics_embed(ctx, new_days, max_window)

        view: Optional[SnipeAnalyticsView] = None
        if len(available_windows) > 1:
            view = SnipeAnalyticsView(
                ctx, refresh, requested_window, available_windows
            )

        message = await ctx.send(embed=embed, view=view)
        if view is not None:
            view.message = message
        return message
