import asyncio
import asyncio
import datetime
import imghdr
import random
from io import BytesIO
from typing import Dict, List, Optional, Tuple, Union

import aiohttp
import asyncpg
import discord
import humanize
from discord import NotFound, app_commands
from discord.ext import commands, tasks

from ...bot import CONFIG, BaseBot
from ...context import BaseContext
from ...embed import BaseEmbed
from ...kernel.views.history import SelectUserLogEvents, UserHistory
from ...kernel.views.meta import Confirmation
from ...kernel.views.paginator import Paginator
from ...kernel.views.todo import SeeTask


class HighlightBlockDashboard(discord.ui.View):
    """Interactive dashboard view for highlight block management."""

    def __init__(
        self,
        bot: BaseBot,
        guild: discord.Guild,
        blocked_map: Dict[int, List[int]],
    ) -> None:
        super().__init__(timeout=180)
        self.bot = bot
        self.guild = guild
        self.blocked_map = blocked_map
        self.mode: str = "all"
        self.message: Optional[discord.Message] = None

    async def start(self, ctx: BaseContext) -> None:
        embed = self._build_embed()
        self.message = await ctx.reply(
            embed=embed,
            view=self,
            mention_author=False,
        )

    def _build_embed(self) -> BaseEmbed:
        description: List[str] = []
        serial = 1
        for user_id, objects in self.blocked_map.items():
            if not objects:
                continue
            actor = self.guild.get_member(user_id)
            if actor is None:
                continue
            for object_id in objects:
                entry_object = (
                    self.guild.get_member(object_id)
                    or self.guild.get_role(object_id)
                )
                if entry_object is None:
                    continue
                if self.mode == "members" and not isinstance(
                    entry_object, discord.Member
                ):
                    continue
                if self.mode == "roles" and not isinstance(
                    entry_object, discord.Role
                ):
                    continue
                description.append(
                    f"**{serial}.** {actor.mention} blocked {entry_object.mention}"
                )
                serial += 1

        if not description:
            description.append("No entries match the current filter.")

        embed = BaseEmbed(
            title="Highlight Block Dashboard",
            description="\n".join(description[:25]),
            colour=self.bot.colour,
        )
        embed.set_footer(text=f"Viewing: {self.mode.title()} entries")
        return embed

    async def _update_view(self, interaction: discord.Interaction) -> None:
        if not self.message:
            return
        await interaction.response.edit_message(
            embed=self._build_embed(),
            view=self,
        )

    @discord.ui.button(label="All", style=discord.ButtonStyle.secondary)
    async def show_all(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        self.mode = "all"
        await self._update_view(interaction)

    @discord.ui.button(label="Members", style=discord.ButtonStyle.primary)
    async def show_members(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        self.mode = "members"
        await self._update_view(interaction)

    @discord.ui.button(label="Roles", style=discord.ButtonStyle.success)
    async def show_roles(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        self.mode = "roles"
        await self._update_view(interaction)


class Utility(commands.Cog):
    """Essesntial commands for easy life on discord."""

    def __init__(self, bot: BaseBot):
        self.bot = bot
        self.context_menu = app_commands.ContextMenu(
            name="Toggle Highlight-Block User",
            callback=self.highlight_block_context_menu,
        )
        self.bot.tree.add_command(self.context_menu)
        self.digest_dispatch_lock = asyncio.Lock()
        self.daily_digest_dispatch.start()
        self.weekly_digest_dispatch.start()

    def cog_unload(self) -> None:
        self.daily_digest_dispatch.cancel()
        self.weekly_digest_dispatch.cancel()

    @staticmethod
    def _parse_duration(duration: Optional[str]) -> Optional[datetime.timedelta]:
        if not duration:
            return None

        duration = duration.strip().lower()
        if duration in {"0", "off", "none"}:
            return datetime.timedelta()

        total_seconds = 0
        current = ""
        for char in duration:
            if char.isdigit():
                current += char
                continue
            if not current:
                return None
            multiplier = {
                "s": 1,
                "m": 60,
                "h": 3600,
                "d": 86400,
            }.get(char)
            if multiplier is None:
                return None
            total_seconds += int(current) * multiplier
            current = ""

        if current:
            total_seconds += int(current)

        if total_seconds <= 0:
            return None
        return datetime.timedelta(seconds=total_seconds)

    @staticmethod
    def _trigger_matches_scope(
        scope_type: Optional[str],
        scope_id: Optional[int],
        message: discord.Message,
    ) -> bool:
        if not scope_type or not scope_id:
            return True

        if scope_type == "channel":
            return message.channel.id == scope_id
        if scope_type == "category":
            return getattr(message.channel, "category_id", None) == scope_id
        return True

    @staticmethod
    def _is_snoozed(
        snooze_until: Optional[datetime.datetime],
    ) -> bool:
        if snooze_until is None:
            return False
        if isinstance(snooze_until, datetime.datetime):
            if snooze_until.tzinfo is None:
                snooze_until = snooze_until.replace(tzinfo=datetime.timezone.utc)
            return snooze_until > discord.utils.utcnow()
        return False

    def _get_digest_preference(
        self,
        guild_id: int,
        user_id: int,
        trigger_digest: Optional[str],
    ) -> str:
        if trigger_digest and trigger_digest != "inherit":
            return trigger_digest

        guild_preferences = self.bot.highlight_preferences.get(guild_id, {})
        preference = guild_preferences.get(user_id, {})
        return preference.get("digest", "immediate")

    async def _queue_digest(
        self,
        guild: discord.Guild,
        user: discord.Member,
        trigger: str,
        message: discord.Message,
        preference: str,
    ) -> None:
        async with self.digest_dispatch_lock:
            guild_queue = self.bot.highlight_digest_cache.setdefault(guild.id, {})
            user_queue = guild_queue.setdefault(user.id, [])
            user_queue.append(
                {
                    "trigger": trigger,
                    "content": message.content[:1000],
                    "channel_id": message.channel.id,
                    "message_url": message.jump_url,
                    "created_at": discord.utils.utcnow(),
                }
            )

            guild_preferences = self.bot.highlight_preferences.setdefault(guild.id, {})
            user_preferences = guild_preferences.setdefault(
                user.id,
                {
                    "digest": preference,
                    "next_dispatch": None,
                },
            )
            user_preferences["digest"] = preference
            next_dispatch = user_preferences.get("next_dispatch")
            now = discord.utils.utcnow()
            delta = datetime.timedelta(days=1 if preference == "daily" else 7)
            if not next_dispatch or next_dispatch <= now:
                user_preferences["next_dispatch"] = now + delta

            try:
                await self.bot.db.execute(
                    """
                    INSERT INTO highlight_preferences (user_id, guild_id, digest, next_dispatch)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (user_id, guild_id)
                    DO UPDATE SET digest = EXCLUDED.digest, next_dispatch = EXCLUDED.next_dispatch
                    """,
                    user.id,
                    guild.id,
                    user_preferences["digest"],
                    user_preferences["next_dispatch"],
                )
            except Exception:
                pass

    async def _refresh_highlight_cache(self) -> None:
        highlight_data = await self.bot.db.fetch("SELECT * FROM highlight")
        if not highlight_data:
            self.bot.highlight = {}
            return

        highlight_data_list: List[Tuple[int, int, Dict[str, Union[str, int, None]]]] = []
        for record in highlight_data:
            record_dict = dict(record)
            highlight_data_list.append(
                (
                    record["guild_id"],
                    record["user_id"],
                    {
                        "trigger": record_dict.get("trigger"),
                        "scope_type": record_dict.get("scope_type"),
                        "scope_id": record_dict.get("scope_id"),
                        "snooze_until": record_dict.get("snooze_until"),
                        "digest": record_dict.get("digest"),
                    },
                )
            )
        self.bot.highlight = self.bot.generate_dict_cache(highlight_data_list)

    async def log_highlight_audit(
        self,
        guild_id: int,
        actor_id: int,
        target_id: int,
        action: str,
        scope: str,
    ) -> None:
        timestamp = discord.utils.utcnow()
        try:
            await self.bot.db.execute(
                "INSERT INTO highlight_audit VALUES ($1, $2, $3, $4, $5, $6)",
                guild_id,
                actor_id,
                target_id,
                action,
                scope,
                timestamp,
            )
        except Exception:
            pass

        channel_id = CONFIG.get("HIGHLIGHT_AUDIT_CHANNEL")
        if not channel_id:
            return
        channel = self.bot.get_channel(int(channel_id))
        if channel is None:
            return

        embed = BaseEmbed(
            title="Highlight Audit Log",
            description=(
                f"Action: **{action.title()}**\n"
                f"Actor: <@{actor_id}>\n"
                f"Target: <@{target_id}>\n"
                f"Scope: `{scope}`"
            ),
            colour=self.bot.colour,
        )
        embed.set_footer(text=f"Logged at {self.bot.timestamp(timestamp, style='F')}")
        try:
            await channel.send(embed=embed)
        except Exception:
            pass

    async def _dispatch_digests(self, frequency: str) -> None:
        now = discord.utils.utcnow()
        delta = datetime.timedelta(days=1 if frequency == "daily" else 7)

        async with self.digest_dispatch_lock:
            queue_snapshot = {
                guild_id: {user_id: list(entries) for user_id, entries in users.items()}
                for guild_id, users in self.bot.highlight_digest_cache.items()
            }

        for guild_id, user_entries in queue_snapshot.items():
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                continue

            for user_id, entries in user_entries.items():
                if not entries:
                    continue

                preference = (
                    self.bot.highlight_preferences.get(guild_id, {}).get(user_id, {})
                )
                if preference.get("digest") != frequency:
                    continue

                next_dispatch = preference.get("next_dispatch")
                if (
                    isinstance(next_dispatch, datetime.datetime)
                    and next_dispatch > now
                ):
                    continue

                member = guild.get_member(user_id)
                user: Optional[discord.abc.User] = member or self.bot.get_user(user_id)
                if user is None:
                    continue

                lines: List[str] = []
                for entry in entries[:15]:
                    channel = guild.get_channel(entry.get("channel_id"))
                    channel_mention = channel.mention if channel else "a deleted channel"
                    lines.append(
                        (
                            f"> `{entry.get('trigger')}` in {channel_mention}\n"
                            f"> [Jump to message]({entry.get('message_url')}) • {self.bot.timestamp(entry.get('created_at'), style='R') if entry.get('created_at') else 'Recently'}"
                        )
                    )

                digest_embed = BaseEmbed(
                    title=f"{guild.name} — {frequency.title()} Highlight Digest",
                    description="\n".join(lines) or "No highlights recorded during this window.",
                    colour=self.bot.colour,
                )

                try:
                    await user.send(embed=digest_embed)
                except discord.HTTPException:
                    continue

                async with self.digest_dispatch_lock:
                    if guild_id in self.bot.highlight_digest_cache:
                        self.bot.highlight_digest_cache[guild_id][user_id] = []

                preference["next_dispatch"] = now + delta
                try:
                    await self.bot.db.execute(
                        """
                        INSERT INTO highlight_preferences (user_id, guild_id, digest, next_dispatch)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT (user_id, guild_id)
                        DO UPDATE SET digest = EXCLUDED.digest, next_dispatch = EXCLUDED.next_dispatch
                        """,
                        user_id,
                        guild_id,
                        frequency,
                        preference["next_dispatch"],
                    )
                except Exception:
                    pass

    @tasks.loop(minutes=30)
    async def daily_digest_dispatch(self) -> None:
        await self._dispatch_digests("daily")

    @tasks.loop(hours=1)
    async def weekly_digest_dispatch(self) -> None:
        await self._dispatch_digests("weekly")

    @daily_digest_dispatch.before_loop
    async def before_daily_digest(self) -> None:
        await self.bot.wait_until_ready()

    @weekly_digest_dispatch.before_loop
    async def before_weekly_digest(self) -> None:
        await self.bot.wait_until_ready()

    @property
    def emote(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name="Tools", id=1026029046146007050, animated=True)

    async def highlight_block_context_menu(
        self, interaction: discord.Interaction, member: discord.Member
    ):
        query: str = "INSERT INTO highlight_blocked VALUES ($1, $2, $3, $4, $5)"
        try:
            await self.bot.db.execute(
                query,
                interaction.user.id,
                interaction.guild.id,
                member.id,
                "member",
                discord.utils.utcnow(),
            )

            await self.log_highlight_audit(
                interaction.guild.id,
                interaction.user.id,
                member.id,
                "block",
                "member",
            )

            # Regenerate the cache after the insert
            highlight_blocked_data = await self.bot.db.fetch(
                "SELECT * FROM highlight_blocked WHERE user_id = $1 AND guild_id = $2",
                interaction.user.id,
                interaction.guild.id,
            )
            if highlight_blocked_data:
                highlight_blocked_data_list: List[Tuple] = [
                    (data["guild_id"], data["user_id"], data["object_id"])
                    for data in highlight_blocked_data
                ]
                self.bot.highlight_blocked = self.bot.generate_dict_cache(
                    highlight_blocked_data_list
                )
            else:
                self.bot.highlight_blocked = {}

            await interaction.response.send_message(
                f"**{member.mention}** - Has now been blocked from highlighting you in **{interaction.guild}** <:SarahPray:907109950248067154>",
                allowed_mentions=self.bot.mentions,
                ephemeral=True,
            )
        except asyncpg.UniqueViolationError:
            await self.bot.db.execute(
                "DELETE FROM highlight_blocked WHERE user_id = $1 AND guild_id = $2 AND object_id = $3",
                interaction.user.id,
                interaction.guild.id,
                member.id,
            )

            await self.log_highlight_audit(
                interaction.guild.id,
                interaction.user.id,
                member.id,
                "unblock",
                "member",
            )

            # Regenerate the cache after the delete
            highlight_blocked_data = await self.bot.db.fetch(
                "SELECT * FROM highlight_blocked WHERE user_id = $1 AND guild_id = $2",
                interaction.user.id,
                interaction.guild.id,
            )
            if highlight_blocked_data:
                highlight_blocked_data_list: List[Tuple] = [
                    (data["guild_id"], data["user_id"], data["object_id"])
                    for data in highlight_blocked_data
                ]
                self.bot.highlight_blocked = self.bot.generate_dict_cache(
                    highlight_blocked_data_list
                )
            else:
                self.bot.highlight_blocked = {}

            return await interaction.response.send_message(
                content=f"Successfully removed {member.mention} from your `highlight blocked` list. {member.mention} will now be able to highlight you <:RavenPray:914410353155244073>",
                allowed_mentions=self.bot.mentions,
                ephemeral=True,
            )

    async def generate_highlight_emb(self, message: discord.Message, user_id: str):
        message_history: List[str] = []
        async for msg in message.channel.history(limit=1):
            stringed_msg = str(msg)
            if user_id in stringed_msg:
                return
            message_history.append(
                f"By: {msg.author.mention}\n At: {self.bot.timestamp(msg.created_at, style='R')}\n Message: {msg.content[:100]}\n"
            )

        highlight_emb = BaseEmbed(
            title=f"You were HIghliGhTeD \U00002728",
            description="".join(message_history[::-1]),
            colour=self.bot.colour,
        )
        return highlight_emb

    async def task_id_autocomplete(
        self, interaction: discord.Interaction, current: int
    ) -> List[app_commands.Choice[int]]:
        task_deets = await self.bot.db.fetch(
            "SELECT (task_id) FROM todo WHERE user_id = $1 ORDER BY task_id ASC",
            interaction.user.id,
        )
        ids = [data[0] for data in task_deets]
        try:
            return [app_commands.Choice(name=ids, value=ids) for ids in ids]
        except NotFound:
            return

    async def trigger_list_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        try:
            cached_entries = self.bot.highlight[interaction.guild.id][
                interaction.user.id
            ]
            choices = []
            seen: set[str] = set()
            for entry in cached_entries:
                trigger_word = entry.get("trigger")
                if not trigger_word:
                    continue
                if current.lower() not in trigger_word:
                    continue
                if trigger_word in seen:
                    continue
                seen.add(trigger_word)
                choices.append(
                    app_commands.Choice(name=trigger_word, value=trigger_word)
                )
            return choices
        except KeyError:
            trigger_list = await self.bot.db.fetch(
                "SELECT * FROM highlight WHERE user_id = $1 AND guild_id = $2",
                interaction.user.id,
                interaction.guild.id,
            )
            names = [str(data["trigger"]) for data in trigger_list]
        try:
            return [
                app_commands.Choice(name=names, value=names)
                for names in names
                if current.lower() in names
            ]
        except NotFound:
            return

    async def highlight_core(self, message: discord.Message):
        """Core functionality for highlight."""
        if message.guild is None:
            return

        if message.author.bot:
            return

        # Could it be any better :troll:
        try:
            author_id = str(message.author.id)
            role_ids = {str(role.id) for role in getattr(message.author, "roles", [])}
            guild_highlight_block = self.bot.highlight_blocked.get(message.guild.id, {})
            blocked_objects = {
                str(obj)
                for objects in guild_highlight_block.values()
                for obj in objects
            }

            if author_id in blocked_objects:
                return

            if role_ids.intersection(blocked_objects):
                return
        except Exception:
            pass

        if self.bot.highlight:
            guild_cache = self.bot.highlight.get(message.guild.id, {})
            if not guild_cache:
                return

            content_lower = message.content.lower()
            now = discord.utils.utcnow()
            for user_id, trigger_entries in guild_cache.items():
                user = message.guild.get_member(user_id)
                if user is None or message.author.id == user.id:
                    continue

                for entry in trigger_entries:
                    trigger_word = entry.get("trigger")
                    if not trigger_word:
                        continue
                    if trigger_word not in content_lower:
                        continue
                    scope_type = entry.get("scope_type")
                    scope_id = entry.get("scope_id")
                    snooze_until = entry.get("snooze_until")

                    if not self._trigger_matches_scope(scope_type, scope_id, message):
                        continue

                    if snooze_until and isinstance(snooze_until, datetime.datetime):
                        if snooze_until <= now:
                            try:
                                await self.bot.db.execute(
                                    """
                                    UPDATE highlight
                                    SET snooze_until = NULL
                                    WHERE user_id = $1 AND guild_id = $2 AND trigger = $3
                                      AND COALESCE(scope_type, '') = COALESCE($4, '')
                                      AND COALESCE(scope_id, 0) = COALESCE($5, 0)
                                    """,
                                    user.id,
                                    message.guild.id,
                                    trigger_word,
                                    scope_type,
                                    scope_id,
                                )
                                entry["snooze_until"] = None
                            except Exception:
                                pass
                        elif self._is_snoozed(snooze_until):
                            continue

                    digest_preference = self._get_digest_preference(
                        message.guild.id,
                        user.id,
                        entry.get("digest"),
                    )

                    highlight_emb = await self.generate_highlight_emb(
                        message, str(user.id)
                    )
                    if not highlight_emb:
                        continue

                    emotes: List[str] = [
                        "<a:Jump:1024989069157077062>",
                        "<a:Click:973748305416835102>",
                        "<a:ChainLink:936158619030941706>",
                        "<a:WumpusVibe:905457020575031358>",
                    ]

                    jump_url_component = discord.ui.View()
                    jump_url_component.add_item(
                        discord.ui.Button(
                            label="Jump to Message",
                            emoji=random.choice(emotes),
                            url=message.jump_url,
                        )
                    )

                    if digest_preference == "immediate":
                        try:
                            await user.send(
                                content=(
                                    f"In {message.channel.mention} for **{message.guild}** "
                                    f"you were highlighted with the word `{trigger_word}`!"
                                ),
                                embed=highlight_emb,
                                view=jump_url_component,
                            )
                        except discord.HTTPException:
                            pass
                    else:
                        await self._queue_digest(
                            message.guild,
                            user,
                            trigger_word,
                            message,
                            digest_preference,
                        )

                    break

    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User):
        if before.display_avatar != after.display_avatar:
            log_avatar = await self.bot.db.fetchval(
                "SELECT avatar FROM user_settings WHERE user_id = $1", after.id
            )
            if log_avatar:
                avatar = await after.display_avatar.read()
                async with aiohttp.ClientSession() as session:
                    avatar_spam_webhook = discord.Webhook.partial(
                        id=CONFIG.get("AVATAR_SPAM_ID"),
                        token=CONFIG.get("AVATAR_SPAM_TOKEN"),
                        session=session,
                    )
                    sent_webhook_message = await avatar_spam_webhook.send(
                        file=discord.File(
                            BytesIO(avatar),
                            filename=f"{after}'s_avatar.{imghdr.what(BytesIO(avatar))}",
                        ),
                        wait=True,
                    )
                    await self.bot.db.execute(
                        "INSERT INTO avatar_history VALUES ($1, $2, $3, $4, $5)",
                        after.id,
                        str(sent_webhook_message.attachments[0]),
                        discord.utils.utcnow(),
                        imghdr.what(BytesIO(avatar)),
                        avatar,
                    )
                    await avatar_spam_webhook.session.close()
        if after.bot:
            bot_avatar = await after.display_avatar.read()
            async with aiohttp.ClientSession() as session:
                bot_avatar_spam_webhook = discord.Webhook.partial(
                    id=CONFIG.get("AVATAR_SPAM_ID"),
                    token=CONFIG.get("AVATAR_SPAM_TOKEN"),
                    session=session,
                )
                sent_webhook_message = await bot_avatar_spam_webhook.send(
                    file=discord.File(
                        BytesIO(bot_avatar),
                        filename=f"{after}'s_avatar.{imghdr.what(BytesIO(bot_avatar))}",
                    ),
                    wait=True,
                )
                await self.bot.db.execute(
                    "INSERT INTO avatar_history VALUES ($1, $2, $3, $4, $5)",
                    after.id,
                    str(sent_webhook_message.attachments[0]),
                    discord.utils.utcnow(),
                    imghdr.what(BytesIO(bot_avatar)),
                    bot_avatar,
                )
                await bot_avatar_spam_webhook.session.close()
            return
        if before.name != after.name:
            log_username = await self.bot.db.fetchval(
                "SELECT username FROM user_settings WHERE user_id = $1", after.id
            )
            if log_username:
                await self.bot.db.execute(
                    "INSERT INTO username_history VALUES ($1, $2, $3)",
                    after.id,
                    after.name,
                    discord.utils.utcnow(),
                )
                return

        # Discord removed discriminators.

        # if before.discriminator != after.discriminator:
        #     log_discriminator = await self.bot.db.fetchval(
        #         "SELECT discriminator FROM user_settings WHERE user_id = $1", after.id
        #     )
        #     if log_discriminator:
        #         await self.bot.db.execute(
        #             "INSERT INTO discriminator_history VALUES ($1, $2, $3)",
        #             after.id,
        #             after.discriminator,
        #             discord.utils.utcnow(),
        #         )
        #         return

    @commands.Cog.listener("on_message")
    async def highlight_on_message(self, message: discord.Message):
        await self.highlight_core(message=message)

    @commands.Cog.listener("on_message_edit")
    async def highlight_on_message_edit(
        self, before: discord.Message, after: discord.Message
    ):
        await self.highlight_core(message=after)

    @commands.hybrid_group(
        name="todo",
        brief="List User's Todo List.",
        aliases=["td"],
        with_app_command=True,
    )
    @app_commands.checks.cooldown(2, 5)
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def todo(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Sends Todo sub - commands"""
        if ctx.invoked_subcommand is None:
            return await ctx.command_help()

    @todo.command(name="add", brief="Add item to your list.", with_app_command=True)
    @app_commands.checks.cooldown(2, 5)
    @commands.cooldown(2, 5, commands.BucketType.user)
    @app_commands.describe(task="The task you want to complete asap.")
    async def todo_add(
        self, ctx: BaseContext, *, task: Optional[str]
    ) -> Optional[discord.Message]:
        """Add tasks to your todo list."""
        if ctx.message.reference:
            task = ctx.message.reference.resolved.content
        if not task:
            return await ctx.reply(
                f"**{ctx.author}** - You have to pass in a `task` so that I can add it to your todo list."
            )
        if len(task) > 500:
            return await ctx.reply(
                f"Please make sure that the `task` is below 400 characters."
            )
        else:
            cleaned_task = task.strip()
            inserted_row = await self.bot.db.fetchrow(
                "INSERT INTO todo (user_id, task, created_at, jump_url) VALUES ($1, $2, $3, $4) "
                "RETURNING task_id, created_at",
                ctx.author.id,
                cleaned_task,
                ctx.message.created_at,
                ctx.message.jump_url,
            )
            todo_add_emb = BaseEmbed(
                title=f"\U00002728 Todo Added",
                description=f"<:ReplyContinued:930634770004725821> **Task ID**: `{inserted_row['task_id']}`\n<:Reply:930634822865547294> **Noted On **: {self.bot.timestamp(inserted_row['created_at'], style='D')}",
                colour=self.bot.colour,
            )
            todo_add_emb.add_field(name="Task :", value=f">>> {cleaned_task}")
            todo_add_emb.set_thumbnail(url=ctx.author.display_avatar.url)

            await ctx.reply(embed=todo_add_emb)

    @todo.command(
        name="show",
        brief="See a task in detail.",
        aliases=["see"],
        with_app_command=True,
    )
    @app_commands.rename(task_id="id")
    @app_commands.describe(task_id="ID of your task.")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @app_commands.autocomplete(task_id=task_id_autocomplete)
    async def todo_see(
        self, ctx: BaseContext, task_id: int
    ) -> Optional[discord.Message]:
        """Check out a task in detail."""
        async with ctx.typing():
            await asyncio.sleep(1)
        if not task_id:
            return await ctx.reply(
                f"**{ctx.author}** - Give me a task id for me to fetch details."
            )
        fetch_task = await self.bot.db.fetch(
            "SELECT * FROM todo WHERE task_id = $1 AND user_id = $2",
            task_id,
            ctx.author.id,
        )
        if not fetch_task:
            return await ctx.reply(
                f"Couldn't find a task id of `{task_id}`. Try running another one."
            )
        for data in fetch_task:
            todo_show_emb = BaseEmbed(
                title=f"\U0001f4dc {ctx.author}'s Task Info",
                description=f"<:ReplyContinued:930634770004725821> **Task ID** : `{data[0]}`\n<:ReplyContinued:930634770004725821> **Jump Url** : [**Click Here**]({data[4]})\n<:Reply:930634822865547294> **Noted On** : {self.bot.timestamp(data[3], style='D')}\n────",
                colour=self.bot.colour,
            )
            todo_show_emb.add_field(
                name="<:Join:932976724235395072> Task :", value=f">>> {data[2]}"
            )
            todo_show_emb.set_thumbnail(url=ctx.author.display_avatar.url)
        todo_see_view = SeeTask(self.bot, ctx, task_id)
        todo_see_view.message = await ctx.reply(embed=todo_show_emb, view=todo_see_view)

    @todo.command(
        name="list", brief="See your todo list.", aliases=["all"], with_app_command=True
    )
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def todo_list(self, ctx: BaseContext) -> Optional[discord.Message]:
        """See your entire todo list."""
        fetch_tasks = await self.bot.db.fetch(
            f"SELECT * FROM todo WHERE user_id = $1 ORDER BY task_id", ctx.author.id
        )
        if not fetch_tasks:
            return await ctx.reply(
                f"You currently have `0` tasks present. To start listing out tasks, run `{ctx.clean_prefix}todo add <task>` <a:LifeSucks:932255208044650596>"
            )

        if len(fetch_tasks) == 1:
            for alpha in fetch_tasks:
                todo_show_emb = BaseEmbed(
                    title=f"\U0001f4dc {ctx.author}'s Task Info",
                    description=f"<:ReplyContinued:930634770004725821> **Task ID**: `{alpha[0]}`\n<:ReplyContinued:930634770004725821> **Jump Url**: [**Click Here**]({alpha[4]})\n<:Reply:930634822865547294> **Noted On**: {self.bot.timestamp(alpha[3], style='D')}\n────",
                    colour=self.bot.colour,
                )
                todo_show_emb.add_field(
                    name="<:Join:932976724235395072> Task:", value=f">>> {alpha[2]}"
                )
                todo_show_emb.set_thumbnail(url=ctx.author.display_avatar.url)
            return await ctx.reply(embed=todo_show_emb, mention_author=False)

        serial_no: int = 0
        embed_list: List = []
        for beta in fetch_tasks:
            serial_no += 1
            todo_embs = BaseEmbed(
                title=f"\U0001f4dc {ctx.author}'s Todo List",
                description=f"<:ReplyContinued:930634770004725821> **Task ID**: `{beta[0]}`\n<:ReplyContinued:930634770004725821> **Jump Url**: [**Click Here**]({beta[4]})\n<:Reply:930634822865547294> **Noted On**: {self.bot.timestamp(beta[3], style='D')}\n────",
                colour=self.bot.colour,
            )
            todo_embs.add_field(name="Task :", value=f">>> {beta[2]}")
            todo_embs.set_thumbnail(url=ctx.author.display_avatar.url)
            todo_embs.set_footer(
                text=f"Task Index: {serial_no} | Run {ctx.clean_prefix}todo for more help"
            )
            embed_list.append(todo_embs)
        await Paginator(self.bot, ctx, embed_list).send(ctx)

    @todo.command(name="edit", brief="Edit task", with_app_command=True)
    @app_commands.rename(task_id="id")
    @app_commands.rename(edited="content")
    @app_commands.describe(task_id="ID of your task.")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @app_commands.autocomplete(task_id=task_id_autocomplete)
    @app_commands.describe(edited="New content for the current task you want to edit.")
    async def todo_edit(
        self, ctx: BaseContext, task_id: int, *, edited: str
    ) -> Optional[discord.Message]:
        """Edit a particular task."""
        async with ctx.typing():
            await asyncio.sleep(0.5)
        if len(edited) > 500:
            return await ctx.reply(
                f"Please make sure that the `edited content` is below 200 characters."
            )
        owned_task_id = await self.bot.db.fetchval(
            "SELECT task_id FROM todo WHERE task_id = $1 AND user_id = $2",
            task_id,
            ctx.author.id,
        )
        if owned_task_id is None:
            await ctx.reply(
                f"<:GeraltRightArrow:904740634982760459> **Task ID -** `{task_id}` - is a task either which you do not own or is not present in the database <:DutchySMH:930620665139191839>"
            )
        else:
            cleaned_edited = edited.strip()
            await self.bot.db.execute(
                "UPDATE todo SET task = $1, jump_url = $2, created_at = $3 WHERE task_id = $4 AND user_id = $5",
                cleaned_edited,
                ctx.message.jump_url,
                ctx.message.created_at,
                task_id,
                ctx.author.id,
            )
            await ctx.reply(f"Successfully edited **Task ID -** `{task_id}`")

    @todo.command(
        name="remove",
        brief="Removes Task",
        aliases=["finished", "done"],
        with_app_command=True,
    )
    @app_commands.rename(task_id="id")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @app_commands.autocomplete(task_id=task_id_autocomplete)
    @app_commands.describe(task_id="ID of the task you've completed")
    async def todo_remove(
        self, ctx: BaseContext, *, task_id: int
    ) -> Optional[discord.Message]:
        """Remove a particular task."""
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{ctx.clean_prefix}{ctx.command}` for the `{ctx.command}` command <:SarahPray:920484222421045258>"

        async def yes(
            ui: discord.ui.View,
            interaction: discord.Interaction,
            button: discord.ui.button,
        ):
            if interaction.user != ctx.author:
                return await interaction.response.send_message(
                    content=f"{pain}", ephemeral=True
                )
            for view in ui.children:
                view.disabled = True
            owned_task_id = await self.bot.db.fetchval(
                "SELECT task_id FROM todo WHERE task_id = $1 AND user_id = $2",
                task_id,
                ctx.author.id,
            )
            if owned_task_id is None:
                await interaction.response.defer()
                return await ui.response.edit(
                    content=f"<:GeraltRightArrow:904740634982760459> Task ID - `{task_id}` : is a task either which you do not own or is not present in the database <a:IPat:933295620834336819>",
                    view=ui,
                )
            else:
                await interaction.response.defer()
                await self.bot.db.execute(
                    "DELETE FROM todo WHERE task_id = $1 AND user_id = $2",
                    task_id,
                    ctx.author.id,
                )
                await ui.response.edit(
                    content=f"Successfully removed Task ID - `{task_id}` <:HaroldSaysOkay:907110916104007681>",
                    view=ui,
                )

        async def no(
            ui: discord.ui.View,
            interaction: discord.Interaction,
            button: discord.ui.button,
        ):
            if interaction.user != ctx.author:
                return await interaction.response.send_message(
                    content=f"{pain}", ephemeral=True
                )
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            await ui.response.edit(
                content=f"Okay then, I haven't removed Task ID - `{task_id}` from your list <:DuckSip:917006564265705482>",
                view=ui,
            )

        Confirmation.response = await ctx.reply(
            f"Are you sure you want to remove Task ID - `{task_id}` from your list <:BallManHmm:933398958263386222>",
            view=Confirmation(ctx, yes, no),
        )

    @todo.command(
        name="clear", brief="Delete Todo Tasks.", aliases=["delete", "del", "cl"]
    )
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def todo_clear(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Delete your entire todo list."""
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{ctx.clean_prefix}{ctx.command}` for the `{ctx.command}` command <:SarahPray:920484222421045258>"
        total = await self.bot.db.fetch(
            f"SELECT * FROM todo WHERE user_id = $1", ctx.author.id
        )
        if total == 0:
            await ctx.reply(
                "You currently have `0` tasks present. To start listing out tasks, run `{ctx.clean_prefix}todo add <task>`"
            )
        else:

            async def yes(
                ui: discord.ui.View,
                interaction: discord.Interaction,
                button: discord.ui.Button,
            ):
                if interaction.user != ctx.author:
                    return await interaction.response.send_message(
                        content=f"{pain}", ephemeral=True
                    )
                fetch_task = await self.bot.db.execute(
                    f"DELETE FROM todo WHERE user_id = $1", ctx.author.id
                )
                for view in ui.children:
                    view.disabled = True
                if not fetch_task:
                    await interaction.response.defer()
                    await ui.response.edit(
                        content=f"You currently have `0` tasks present. To start listing out tasks, run `{ctx.clean_prefix}todo add <TASK>` <a:CoffeeSip:907110027951742996>",
                        view=ui,
                    )
                else:
                    await interaction.response.defer()
                    await ui.response.edit(
                        content=f"Successfully deleted `{len(total)}` tasks from your list <:ICool:940786050681425931>.",
                        view=ui,
                    )

            async def no(
                ui: discord.ui.View,
                interaction: discord.Interaction,
                button: discord.ui.button,
            ):
                if interaction.user != ctx.author:
                    return await interaction.response.send_message(
                        content=f"{pain}", ephemeral=True
                    )
                for view in ui.children:
                    view.disabled = True
                await interaction.response.defer()
                await ui.response.edit(
                    content="Okay then, I haven't deleted any `tasks` from your list <a:IEat:940413722537644033>",
                    view=ui,
                )

        Confirmation.response = await ctx.reply(
            f"Are you sure you want to delete a total of `{len(total)}` tasks in your list <a:IThink:933315875501641739>",
            view=Confirmation(ctx, yes, no),
        )

    @commands.hybrid_command(name="afk", brief="Sets you afk.", with_app_command=True)
    @app_commands.describe(reason="Reason why you're going afk.")
    async def afk(self, ctx: BaseContext, *, reason: Optional[str]):
        """Sets you afk."""
        await ctx.add_nanotick()
        await ctx.reply(f"Your afk has been set. Please enjoy!", mention_author=False)
        if not reason:
            reason = "Not Specified . . ."
        query = "INSERT INTO afk VALUES ($1, $2, $3)"
        timestamp = discord.utils.utcnow()
        try:
            await self.bot.db.execute(query, ctx.author.id, reason, timestamp)
        except asyncpg.UniqueViolationError:
            await self.bot.db.execute(
                "UPDATE afk SET reason = $2, queried_at = $3 WHERE user_id = $1",
                ctx.author.id,
                reason,
                timestamp,
            )

        self.bot.afk[ctx.author.id] = (reason, timestamp)

    @commands.hybrid_group(
        name="userlog",
        brief="Logging user updates.",
        aliases=["settings", "tg", "toggle"],
        with_app_command=True,
    )
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def userlog(self, ctx: BaseContext):
        """Opt - in or out for global user update logging."""
        if ctx.invoked_subcommand is None:
            userlog_emb = BaseEmbed(
                title="User Logging",
                description=f"By clicking on the buttons below, you are accepting to store changes made to your `username`, `profile picture`, and `discriminator`.\n\n"
                f"You can opt out of them at anytime and delete every information present",
                colour=self.bot.colour,
            )
            userlog_emb.set_thumbnail(url=ctx.me.display_avatar.url)
            userlog_emb.set_footer(
                text=f'Run "{ctx.clean_prefix}help userlog" for more help'
            )
            return await ctx.send(
                embed=userlog_emb, view=SelectUserLogEvents(self.bot, ctx)
            )

    @userlog.command(
        name="all", brief="Opt - in/out for all events.", with_app_command=True
    )
    async def userlog_all(self, ctx: BaseContext):
        """Opt - in/out for all events."""
        query = (
            "INSERT INTO user_settings (user_id, discriminator, username, avatar) VALUES ($1, $2, $2, $2) "
            "ON CONFLICT (user_id) "
            "DO UPDATE SET avatar = $2, username = $2, discriminator = $2"
        )
        await ctx.add_nanotick()
        await self.bot.db.execute(query, ctx.author.id, True)
        await ctx.reply(f"**{ctx.author}** - Successfully Opted in for all events")

    @userlog.command(
        name="avatar", brief="Opt - in/out for avatar logging.", with_app_command=True
    )
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def userlog_avatar(self, ctx: BaseContext):
        """Opt - in/out for avatar logging."""
        query = (
            "INSERT INTO user_settings (user_id, avatar) VALUES ($1, $2) "
            "ON CONFLICT (user_id) "
            "DO UPDATE SET avatar = $2"
        )
        data = await self.bot.db.fetchval(
            "SELECT avatar FROM user_settings WHERE user_id = $1", ctx.author.id
        )
        if data:
            await self.bot.db.execute(query, ctx.author.id, False)
            await ctx.reply(
                f"**{ctx.author}** - Successfully `opted out` from avatar logging <:TokoOkay:898611996163985410>"
            )
            return await ctx.add_nanotick()

        await self.bot.db.execute(query, ctx.author.id, True)
        await ctx.reply(
            f"**{ctx.author}** - Successfully `opted in` for avatar logging <:DuckThumbsUp:917007413259956254>"
        )
        await ctx.add_nanotick()

    @userlog.command(
        name="username",
        brief="Opt - in/out for username logging.",
        with_app_command=True,
    )
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def userlog_username(self, ctx: BaseContext):
        """Opt - in/out for username logging."""
        query = (
            "INSERT INTO user_settings (user_id, username) VALUES ($1, $2) "
            "ON CONFLICT (user_id) "
            "DO UPDATE SET username = $2"
        )
        data = await self.bot.db.fetchval(
            "SELECT username FROM user_settings WHERE user_id = $1", ctx.author.id
        )
        if data:
            await self.bot.db.execute(query, ctx.author.id, False)
            await ctx.reply(
                f"**{ctx.author}** - Successfully `opted out` from username logging <:TokoOkay:898611996163985410>"
            )
            return await ctx.add_nanotick()

        await self.bot.db.execute(query, ctx.author.id, True)
        await ctx.reply(
            f"**{ctx.author}** - Successfully `opted in` for username logging <:DuckThumbsUp:917007413259956254>"
        )
        return await ctx.add_nanotick()

    # Again discord removed discriminators
    # @userlog.command(
    #     name="discriminator",
    #     brief="Opt - in/out for discriminator logging.",
    #     with_app_command=True,
    # )
    # @commands.cooldown(2, 15, commands.BucketType.user)
    # async def userlog_discriminator(self, ctx: BaseContext):
    #     """Opt - in/out for discriminator logging."""
    #     query = (
    #         "INSERT INTO user_settings (user_id, discriminator) VALUES ($1, $2) "
    #         "ON CONFLICT (user_id) "
    #         "DO UPDATE SET discriminator = $2"
    #     )
    #     data = await self.bot.db.fetchval(
    #         "SELECT discriminator FROM user_settings WHERE user_id = $1", ctx.author.id
    #     )
    #     if data:
    #         await self.bot.db.execute(query, ctx.author.id, False)
    #         await ctx.reply(
    #             f"**{ctx.author}** - Successfully `opted out` from discriminator logging <:TokoOkay:898611996163985410>"
    #         )
    #         return await ctx.add_nanotick()

    #     await self.bot.db.execute(query, ctx.author.id, True)
    #     await ctx.reply(
    #         f"**{ctx.author}** - Successfully `opted in` for discriminator logging <:DuckThumbsUp:917007413259956254>"
    #     )
    #     return await ctx.add_nanotick()

    @userlog.command(name="status", brief="Shows your settings", with_app_command=True)
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def userlog_status(self, ctx: BaseContext):
        """See what details I'm logging about you."""
        fetch_deets = await self.bot.db.fetch(
            "SELECT * FROM user_settings WHERE user_id = $1", ctx.author.id
        )
        data = [
            f"**Avatar Logging :** `{deets[3]}`\n**Username Logging :** `{deets[2]}`\n**Discriminator Logging :** `{deets[1]}`"
            for deets in fetch_deets
        ]
        if not fetch_deets:
            return await ctx.reply(
                f"**{ctx.author}** - You haven't enabled logging at all. Please run `{ctx.clean_prefix}log` for more info."
            )
        log_status = BaseEmbed(
            title=f":scroll: {ctx.author}'s Log Status",
            description="".join(data),
            colour=self.bot.colour,
        )
        log_status.set_thumbnail(url=ctx.author.display_avatar)
        await ctx.reply(embed=log_status, mention_author=False)

    @userlog.command(
        name="delete", brief="Delete all data", aliases=["reset"], with_app_command=True
    )
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def userlog_delete(self, ctx: BaseContext):
        """Delete your logged data."""

        async def yes(
            ui: discord.ui.View,
            interaction: discord.Interaction,
            button: discord.ui.Button,
        ):
            await self.bot.db.execute(
                "DELETE FROM avatar_history WHERE user_id = $1", ctx.author.id
            )
            await self.bot.db.execute(
                "DELETE FROM username_history WHERE user_id = $1", ctx.author.id
            )
            await self.bot.db.execute(
                "DELETE FROM discriminator_history WHERE user_id = $1", ctx.author.id
            )
            await self.bot.db.execute(
                "DELETE FROM user_settings WHERE user_id = $1", ctx.author.id
            )
            await ctx.add_nanotick()
            for view in ui.children:
                view.disabled = True
            await ui.response.edit(
                content=f"Successfully deleted your logged data", view=ui
            )

        async def no(
            ui: discord.ui.View,
            interaction: discord.Interaction,
            button: discord.ui.Button,
        ):
            for view in ui.children:
                view.disabled = True
            await ui.response.edit(
                content=f"Seems like I'm not deleting your data.", view=ui
            )
            await ctx.add_nanocross()

        Confirmation.response = await ctx.reply(
            f"Are you sure you want to delete your data?",
            view=Confirmation(ctx, yes, no),
            allowed_mentions=self.bot.mentions,
        )

    @commands.hybrid_command(
        name="userhistory",
        brief="Get history of user.",
        aliases=["uhy"],
        with_app_command=True,
    )
    @app_commands.checks.cooldown(3, 15)
    @commands.cooldown(3, 15, commands.BucketType.user)
    @app_commands.describe(user="The user you want to get information on.")
    async def user_history(
        self, ctx: BaseContext, *, user: Optional[discord.User] = None
    ):
        """Get entire history of a user."""
        user = user or ctx.author
        history_emb = BaseEmbed(
            title=f"\U0001f4dc {user}'s History",
            description=f"> [**Avatar**]({user.display_avatar.url})\n "
            f"> **Created on:** {self.bot.timestamp(user.created_at, style = 'D')} ({self.bot.timestamp(user.created_at, style = 'R')}) \n",
            colour=self.bot.colour,
        )
        history_emb.set_image(url=user.display_avatar.url)
        await ctx.send(embed=history_emb, view=UserHistory(self.bot, ctx, user))

    @commands.hybrid_command(
        name="avatarhistory",
        brief="Get Avatar History of User.",
        aliases=["avhy"],
        with_app_command=True,
    )
    @app_commands.describe(user="The user you want to see the avatar history of.")
    async def avatar_history(
        self,
        ctx: BaseContext,
        *,
        user: Optional[Union[discord.User, discord.Member]] = None,
    ):
        """Get paginated view of all PFPs of a user."""
        user = user or ctx.author
        if ctx.message.reference:
            user = ctx.message.reference.resolved.author

        if not user.bot:
            log_avatar = await self.bot.db.fetchval(
                "SELECT avatar FROM user_settings WHERE user_id = $1", user.id
            )
            if not log_avatar:
                return await ctx.reply(
                    f"**{user}** - Hasn't `opted in` for avatar logging. Tell them to run `{ctx.clean_prefix}userlog avatar` <:TokoOkay:898611996163985410>"
                )

        avatar_history = await self.bot.db.fetch(
            "SELECT * FROM avatar_history WHERE user_id = $1", user.id
        )
        if not avatar_history:
            return await ctx.reply(
                f"**{user}** - has no records of previous avatars <:ForPatricksSake:915845797533335552> Please wait until they change their pfp atleast once \U0001f91d"
            )

        if len(avatar_history) == 1:
            for x in avatar_history:
                avatar_history_emb = BaseEmbed(
                    title=f"{user}'s Avatar",
                    description=f"<:GeraltRightArrow:904740634982760459> **Changed:** {self.bot.timestamp(x[2], style='D')} | `{humanize.naturaltime(discord.utils.utcnow() - x[2])}`",
                    colour=self.bot.colour,
                )
                avatar_history_emb.set_image(url=x[1])
                avatar_history_emb.set_footer(text=f"Format: {x[3].capitalize()}")
                return await ctx.reply(embed=avatar_history_emb)

        embed_list: List[BaseEmbed] = []
        serial_no: int = 1
        for y in avatar_history:
            avatar_history_embs = BaseEmbed(
                title=f"\U0001f4dc {user}'s Avatars",
                description=f"<:GeraltRightArrow:904740634982760459> **Changed:** {self.bot.timestamp(y[2], style='D')} | `{humanize.naturaltime(discord.utils.utcnow() - y[2])}`",
                colour=self.bot.colour,
            )
            avatar_history_embs.set_image(url=y[1])
            avatar_history_embs.set_footer(
                text=f"Format: {y[3].capitalize()} | Avatar No.: {serial_no}"
            )
            embed_list.append(avatar_history_embs)
            serial_no += 1
        await Paginator(self.bot, ctx, embeds=embed_list).send(ctx)

    @commands.hybrid_group(
        name="highlight", brief="Get notified", aliases=["hl"], with_app_command=True
    )
    async def highlight(self, ctx: BaseContext):
        """Get notified by triggered words!"""
        if ctx.invoked_subcommand is None:
            return await ctx.command_help()

    @highlight.command(
        name="add", brief="Add triggers", aliases=["set"], with_app_command=True
    )
    @app_commands.autocomplete(trigger=trigger_list_autocomplete)
    @app_commands.describe(
        trigger="Add a trigger word. Make sure it's not in the list above",
        channel="Only alert when the trigger happens in this channel",
        category="Only alert when the trigger happens in this category",
        snooze="Optional snooze window like 30m, 2h, 1d",
        digest="Override how highlight notifications are delivered",
    )
    @app_commands.choices(
        digest=[
            app_commands.Choice(name="Immediate DM", value="immediate"),
            app_commands.Choice(name="Daily Digest", value="daily"),
            app_commands.Choice(name="Weekly Digest", value="weekly"),
            app_commands.Choice(name="Inherit Preference", value="inherit"),
        ]
    )
    async def highlight_add(
        self,
        ctx: BaseContext,
        trigger: Optional[str] = None,
        channel: Optional[discord.TextChannel] = None,
        category: Optional[discord.CategoryChannel] = None,
        snooze: Optional[str] = None,
        digest: Optional[app_commands.Choice[str]] = None,
    ):
        """Add trigger words with optional scoping and snoozing."""

        if not trigger:
            return await ctx.reply(
                f"**{ctx.author}** - Please mention something for me to add it to your `highlight list` <:RageKill:917007995571961866>"
            )

        trigger = trigger.strip().lower()
        if len(trigger) > 25:
            return await ctx.reply(
                f"**{ctx.author}** - this is not an essay writing competition! Trigger should be less than 15 characters <:SarahPout:990514983978827796>"
            )

        if channel and category:
            return await ctx.reply(
                "Please choose either a `channel` or a `category` scope, not both."
            )

        scope_type: Optional[str] = None
        scope_id: Optional[int] = None
        if channel:
            scope_type, scope_id = "channel", channel.id
        elif category:
            scope_type, scope_id = "category", category.id

        snooze_delta = self._parse_duration(snooze)
        if snooze and snooze_delta is None:
            return await ctx.reply(
                "I couldn't understand that snooze duration. Try formats like `30m`, `2h`, or `1d`."
            )

        snooze_until: Optional[datetime.datetime]
        if snooze_delta:
            snooze_until = discord.utils.utcnow() + snooze_delta
        else:
            snooze_until = None

        digest_value = (
            digest.value if isinstance(digest, app_commands.Choice) else digest
        ) or "inherit"
        if digest_value not in {"immediate", "daily", "weekly", "inherit"}:
            return await ctx.reply("Invalid digest preference provided.")

        existing = self.bot.highlight.get(ctx.guild.id, {}).get(ctx.author.id, [])
        for entry in existing:
            if (
                entry.get("trigger") == trigger
                and entry.get("scope_type") == scope_type
                and entry.get("scope_id") == scope_id
            ):
                return await ctx.reply(
                    "You've already added that trigger with the same scope."
                )

        try:
            await self.bot.db.execute(
                """
                INSERT INTO highlight (
                    user_id,
                    guild_id,
                    trigger,
                    scope_type,
                    scope_id,
                    snooze_until,
                    digest,
                    created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                ctx.author.id,
                ctx.guild.id,
                trigger,
                scope_type,
                scope_id,
                snooze_until,
                None if digest_value == "inherit" else digest_value,
                discord.utils.utcnow(),
            )
        except asyncpg.UniqueViolationError:
            return await ctx.reply(
                f"`{trigger}` - is a trigger word which is already set. Please set another word <:ICool:940786050681425931>"
            )
        except Exception as error:
            return await ctx.reply(f"```py\n{error}\n```")

        await self._refresh_highlight_cache()

        scope_fragment = "anywhere"
        if scope_type == "channel" and scope_id:
            channel_obj = ctx.guild.get_channel(scope_id)
            if channel_obj:
                scope_fragment = f"{channel_obj.mention}"
        elif scope_type == "category" and scope_id:
            category_obj = ctx.guild.get_channel(scope_id)
            if category_obj:
                scope_fragment = f"the `{category_obj.name}` category"

        snooze_fragment = (
            f" and snoozed until {self.bot.timestamp(snooze_until, style='R')}"
            if snooze_until
            else ""
        )

        digest_fragment = {
            "immediate": "with instant DMs",
            "daily": "with daily digests",
            "weekly": "with weekly digests",
            "inherit": "using your default digest settings",
        }[digest_value]

        await ctx.reply(
            f"**{ctx.author}** - Added `{trigger}` scoped to {scope_fragment}{snooze_fragment} {digest_fragment}.",
            delete_after=10,
        )

    @highlight.command(
        name="remove", brief="Remove triggers", aliases=["del"], with_app_command=True
    )
    @app_commands.autocomplete(trigger=trigger_list_autocomplete)
    @app_commands.describe(
        trigger="Remove a trigger word. Make sure it's in the list above",
        channel="Specify the channel scope if the trigger is scoped",
        category="Specify the category scope if the trigger is scoped",
    )
    async def highlight_remove(
        self,
        ctx: BaseContext,
        trigger: Optional[str] = None,
        channel: Optional[discord.TextChannel] = None,
        category: Optional[discord.CategoryChannel] = None,
    ):
        """Remove trigger words to notify you."""

        if not trigger:
            return await ctx.reply(
                f"**{ctx.author}** - Please mention something for me to remove it from your `highlight list`!"
            )

        if channel and category:
            return await ctx.reply(
                "Please choose either a `channel` or a `category` scope when removing a trigger."
            )

        trigger = trigger.strip().lower()
        scope_type = None
        scope_id = None
        if channel:
            scope_type, scope_id = "channel", channel.id
        elif category:
            scope_type, scope_id = "category", category.id

        existing = self.bot.highlight.get(ctx.guild.id, {}).get(ctx.author.id, [])
        target_entry = None
        for entry in existing:
            if (
                entry.get("trigger") == trigger
                and (scope_type or entry.get("scope_type") is None)
                and (scope_id or entry.get("scope_id") is None)
            ):
                if scope_type and entry.get("scope_type") != scope_type:
                    continue
                if scope_id and entry.get("scope_id") != scope_id:
                    continue
                target_entry = entry
                break

        if target_entry is None:
            return await ctx.reply(
                f"**{trigger}** - is not present with the supplied scope. Use `{ctx.clean_prefix}highlight list` to view your triggers."
            )

        try:
            await self.bot.db.execute(
                """
                DELETE FROM highlight
                WHERE user_id = $1
                  AND guild_id = $2
                  AND trigger = $3
                  AND COALESCE(scope_type, '') = COALESCE($4, '')
                  AND COALESCE(scope_id, 0) = COALESCE($5, 0)
                """,
                ctx.author.id,
                ctx.guild.id,
                trigger,
                scope_type,
                scope_id,
            )
        except Exception as error:
            return await ctx.reply(f"```py\n{error}\n```")

        await self._refresh_highlight_cache()

        await ctx.reply(
            f"**{ctx.author}** - Removed `{trigger}` from your list <a:IEat:940413722537644033>",
            delete_after=5,
        )

    @highlight.command(
        name="snooze",
        brief="Temporarily pause a trigger",
        with_app_command=True,
    )
    @app_commands.autocomplete(trigger=trigger_list_autocomplete)
    @app_commands.describe(
        trigger="Choose the trigger you wish to snooze",
        duration="Duration such as 30m, 2h, 1d, or off",
        channel="Optional channel scope if the trigger is scoped",
        category="Optional category scope if the trigger is scoped",
    )
    async def highlight_snooze(
        self,
        ctx: BaseContext,
        trigger: Optional[str] = None,
        duration: Optional[str] = None,
        channel: Optional[discord.TextChannel] = None,
        category: Optional[discord.CategoryChannel] = None,
    ):
        """Allow members to snooze highlight triggers on demand."""

        if not trigger or not duration:
            return await ctx.reply(
                "Please specify both a trigger and a duration. Example: `highlight snooze raid 2h`."
            )

        if channel and category:
            return await ctx.reply(
                "Please choose either a `channel` or a `category` scope when snoozing a trigger."
            )

        trigger = trigger.strip().lower()
        scope_type = None
        scope_id = None
        if channel:
            scope_type, scope_id = "channel", channel.id
        elif category:
            scope_type, scope_id = "category", category.id

        snooze_delta = self._parse_duration(duration)
        if snooze_delta is None:
            return await ctx.reply(
                "I couldn't understand that snooze duration. Try formats like `30m`, `2h`, or `1d`."
            )

        snooze_until = None
        if snooze_delta.total_seconds() > 0:
            snooze_until = discord.utils.utcnow() + snooze_delta

        existing = self.bot.highlight.get(ctx.guild.id, {}).get(ctx.author.id, [])
        match = None
        for entry in existing:
            if (
                entry.get("trigger") == trigger
                and (scope_type or entry.get("scope_type") is None)
                and (scope_id or entry.get("scope_id") is None)
            ):
                if scope_type and entry.get("scope_type") != scope_type:
                    continue
                if scope_id and entry.get("scope_id") != scope_id:
                    continue
                match = entry
                break

        if match is None:
            return await ctx.reply(
                f"I couldn't find `{trigger}` with that scope. Use `{ctx.clean_prefix}highlight list` to review your triggers."
            )

        try:
            await self.bot.db.execute(
                """
                UPDATE highlight
                SET snooze_until = $1
                WHERE user_id = $2
                  AND guild_id = $3
                  AND trigger = $4
                  AND COALESCE(scope_type, '') = COALESCE($5, '')
                  AND COALESCE(scope_id, 0) = COALESCE($6, 0)
                """,
                snooze_until,
                ctx.author.id,
                ctx.guild.id,
                trigger,
                scope_type,
                scope_id,
            )
        except Exception as error:
            return await ctx.reply(f"```py\n{error}\n```")

        await self._refresh_highlight_cache()

        if snooze_until is None:
            message = f"Removed the snooze from `{trigger}`."
        else:
            message = (
                f"Snoozed `{trigger}` until {self.bot.timestamp(snooze_until, style='R')}."
            )
        await ctx.reply(message)

    @highlight.command(
        name="list", brief="List Your Triggers", aliases=["all"], with_app_command=True
    )
    async def highlight_list_triggers(self, ctx: BaseContext):
        """See all of your trigger words."""

        trigger_data = await self.bot.db.fetch(
            "SELECT * FROM highlight WHERE user_id = $1 AND guild_id = $2",
            ctx.author.id,
            ctx.guild.id,
        )
        if not trigger_data:
            return await ctx.reply(
                f"**{ctx.author}** - You have not set any `triggers` <a:IWait:948253556190904371> Please run `{ctx.clean_prefix}highlight add` <:KeanuCool:910026122383728671>"
            )

        now = discord.utils.utcnow()
        entries: List[str] = []
        for record in trigger_data:
            data = dict(record)
            trigger_word = data.get("trigger")
            scope_type = data.get("scope_type")
            scope_id = data.get("scope_id")
            snooze_until = data.get("snooze_until")
            digest = data.get("digest") or self._get_digest_preference(
                ctx.guild.id,
                ctx.author.id,
                None,
            )

            scope_fragment = "anywhere"
            if scope_type == "channel" and scope_id:
                channel = ctx.guild.get_channel(scope_id)
                if channel:
                    scope_fragment = channel.mention
            elif scope_type == "category" and scope_id:
                category = ctx.guild.get_channel(scope_id)
                if category:
                    scope_fragment = f"`{category.name}`"

            snooze_fragment = ""
            if snooze_until and isinstance(snooze_until, datetime.datetime):
                if snooze_until > now:
                    snooze_fragment = (
                        f" (snoozed until {self.bot.timestamp(snooze_until, style='R')})"
                    )

            digest_fragment = {
                "immediate": "Immediate",
                "daily": "Daily digest",
                "weekly": "Weekly digest",
            }.get(digest or "immediate", "Immediate")

            entries.append(
                f"> <:GeraltRightArrow:904740634982760459> `{trigger_word}` in {scope_fragment} — {digest_fragment}{snooze_fragment}"
            )

        trigger_list_emb = BaseEmbed(
            title=f"{ctx.author}'s Trigger List",
            description="\n".join(entries[:15]),
            colour=self.bot.colour,
        )
        trigger_list_emb.set_footer(
            text="Use highlight remove to delete or highlight snooze to pause alerts."
        )
        await ctx.reply(embed=trigger_list_emb, delete_after=10)

    @highlight.command(
        name="digest",
        brief="Control highlight digests",
        with_app_command=True,
    )
    @app_commands.describe(
        frequency="Choose how often you'd like to receive highlight notifications",
    )
    @app_commands.choices(
        frequency=[
            app_commands.Choice(name="Immediate DM", value="immediate"),
            app_commands.Choice(name="Daily Digest", value="daily"),
            app_commands.Choice(name="Weekly Digest", value="weekly"),
        ]
    )
    async def highlight_digest(
        self,
        ctx: BaseContext,
        frequency: Union[str, app_commands.Choice[str]],
    ):
        """Configure the cadence of highlight notifications."""

        choice = frequency.value if isinstance(frequency, app_commands.Choice) else frequency
        choice = choice.lower()
        if choice not in {"immediate", "daily", "weekly"}:
            return await ctx.reply(
                "Please choose between `immediate`, `daily`, or `weekly` delivery."
            )

        now = discord.utils.utcnow()
        next_dispatch = None
        if choice == "daily":
            next_dispatch = now + datetime.timedelta(days=1)
        elif choice == "weekly":
            next_dispatch = now + datetime.timedelta(days=7)

        try:
            await self.bot.db.execute(
                """
                INSERT INTO highlight_preferences (user_id, guild_id, digest, next_dispatch)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id, guild_id)
                DO UPDATE SET digest = EXCLUDED.digest, next_dispatch = EXCLUDED.next_dispatch
                """,
                ctx.author.id,
                ctx.guild.id,
                choice,
                next_dispatch,
            )
        except Exception as error:
            return await ctx.reply(f"```py\n{error}\n```")

        guild_preferences = self.bot.highlight_preferences.setdefault(ctx.guild.id, {})
        guild_preferences[ctx.author.id] = {
            "digest": choice,
            "next_dispatch": next_dispatch,
        }

        if choice == "immediate":
            async with self.digest_dispatch_lock:
                guild_queue = self.bot.highlight_digest_cache.get(ctx.guild.id, {})
                if ctx.author.id in guild_queue:
                    guild_queue.pop(ctx.author.id, None)

        await ctx.reply(
            f"We'll deliver your highlight notifications `{choice}`.",
            delete_after=6,
        )

    @highlight.command(
        name="block",
        brief="Block Objects",
        aliases=["lock", "blacklist", "bl"],
        with_app_command=True,
    )
    @app_commands.describe(
        object="Member or Role you want to block from highlighting you."
    )
    async def highlight_block(
        self, ctx: BaseContext, *, object: Union[discord.Member, discord.Role]
    ):
        """Block users or roles from highlighting you!"""
        if object.bot:
            return await ctx.reply(
                content=f"{object.mention} is a bot <a:IPat:933295620834336819> Please choose a human this time."
            )

        if not object:
            return await ctx.reply(
                f"**{ctx.author}** - Please pass in an `object` for blocking highlights from them <:RageKill:917007995571961866>"
            )

        if ctx.author.id == object.id:
            return await ctx.reply(
                f"**{ctx.author}** - You do realise that you cannot highlight yourself right <a:IPat:933295620834336819>"
            )

        query: str = "INSERT INTO highlight_blocked VALUES ($1, $2, $3, $4, $5)"
        if ctx.guild.get_role(object.id):
            try:
                await ctx.add_nanotick()
                await self.bot.db.execute(
                    query,
                    ctx.author.id,
                    ctx.guild.id,
                    object.id,
                    "role",
                    discord.utils.utcnow(),
                )
                await self.log_highlight_audit(
                    ctx.guild.id,
                    ctx.author.id,
                    object.id,
                    "block",
                    "role",
                )
                await ctx.reply(
                    f"**{object.mention}** - Has now been blocked from highlighting you in **{ctx.guild}** <:SarahPray:907109950248067154>",
                    allowed_mentions=self.bot.mentions,
                )
            except asyncpg.UniqueViolationError:
                await ctx.add_nanocross()
                return await ctx.reply(
                    f"{object.mention} - Has already been blocked from highlighting you <:SIDGoesHmmMan:967421008137056276>",
                    allowed_mentions=self.bot.mentions,
                )

        if ctx.guild.get_member(object.id):
            try:
                await ctx.add_nanotick()
                await self.bot.db.execute(
                    query,
                    ctx.author.id,
                    ctx.guild.id,
                    object.id,
                    "member",
                    discord.utils.utcnow(),
                )
                await self.log_highlight_audit(
                    ctx.guild.id,
                    ctx.author.id,
                    object.id,
                    "block",
                    "member",
                )
                await ctx.reply(
                    f"**{object.mention}** - Has now been blocked from highlighting you in **{ctx.guild}** <:SarahPray:907109950248067154>",
                    allowed_mentions=self.bot.mentions,
                )
            except asyncpg.UniqueViolationError:
                await ctx.add_nanocross()
                return await ctx.reply(
                    f"{object.mention} - Has already been blocked from highlighting you <:SIDGoesHmmMan:967421008137056276>",
                    allowed_mentions=self.bot.mentions,
                )

        highlight_blocked_data = await self.bot.db.fetch(
            "SELECT * FROM highlight_blocked"
        )
        if highlight_blocked_data:
            highlight_blocked_data_list: List = [
                (data["guild_id"], data["user_id"], data["object_id"])
                for data in highlight_blocked_data
            ]
            self.bot.highlight_blocked = self.bot.generate_dict_cache(
                highlight_blocked_data_list
            )

    @highlight.command(
        name="unblock",
        brief="Unblock Objects",
        aliases=["unlock", "whitelist", "whl"],
        with_app_command=True,
    )
    @app_commands.describe(
        object="Member or Role you want to unblock from highlighting you."
    )
    async def highlight_unblock(
        self, ctx: BaseContext, *, object: Union[discord.Member, discord.Role]
    ):
        """Unblock users or roles from highlighting you!"""
        if object.bot:
            return await ctx.reply(
                content=f"{object.mention} is a bot <a:IPat:933295620834336819> Please choose a human this time."
            )

        if not object:
            return await ctx.reply(
                f"**{ctx.author}** - Please pass in an `object` for unblocking highlights from them <:FrogGoesHmmMan:925366780422152232>"
            )

        query = "DELETE FROM highlight_blocked WHERE user_id = $1 AND guild_id = $2 AND object_id = $3"
        try:
            await self.bot.db.execute(query, ctx.author.id, ctx.guild.id, object.id)
            await self.log_highlight_audit(
                ctx.guild.id,
                ctx.author.id,
                object.id,
                "unblock",
                "role" if isinstance(object, discord.Role) else "member",
            )
            await ctx.reply(
                f"Successfully removed {object.mention} from your `highlight blocked` list. {object.mention} will now be able to highlight you <:RavenPray:914410353155244073>",
                allowed_mentions=self.bot.mentions,
            )
            await ctx.add_nanotick()
        except Exception as error:
            return await ctx.reply(f"```py\n{error}\n```")

        highlight_blocked_data = await self.bot.db.fetch(
            "SELECT * FROM highlight_blocked"
        )
        if highlight_blocked_data:
            highlight_blocked_data_list: List = [
                (data["guild_id"], data["user_id"], data["object_id"])
                for data in highlight_blocked_data
            ]
            self.bot.highlight_blocked = self.bot.generate_dict_cache(
                highlight_blocked_data_list
            )
        else:
            self.bot.highlight_blocked = {}

    @highlight.command(
        name="blacklisted",
        brief="Get blocked members.",
        aliases=["blocked-list", "blcklist", "blocked"],
        with_app_command=True,
    )
    async def highlight_blocked_list(self, ctx: BaseContext):
        """Returns List of objects you've blocked."""
        fetch_blacklisted = await self.bot.db.fetch(
            "SELECT * FROM highlight_blocked WHERE user_id = $1 AND guild_id = $2",
            ctx.author.id,
            ctx.guild.id,
        )
        if not fetch_blacklisted:
            return await ctx.reply(
                f"**{ctx.author}** - You have not blocked anyone from highlighting you in **{ctx.guild}** <:ISus:915817563307515924>"
            )

        blacklisted: List = []
        serial_no: int = 0
        for data in fetch_blacklisted:
            serial_no += 1
            if ctx.guild.get_role(data[2]):
                blacklisted.append(
                    f"> **{serial_no}.** Object: <@&{data[2]}>\n> Queried At: {self.bot.timestamp(data[4], style='R')}\n────\n"
                )
            if ctx.guild.get_member(data[2]):
                blacklisted.append(
                    f"> **{serial_no}.** Object: <@{data[2]}>\n> Queried At: {self.bot.timestamp(data[4], style='R')}\n────\n"
                )

        if serial_no <= 3:
            blacklisted_emb = BaseEmbed(
                title=f"\U0001f4dc {ctx.author}'s Block List",
                description="".join(blacklisted),
                colour=self.bot.colour,
            )
            blacklisted_emb.set_thumbnail(url=ctx.author.display_avatar.url)
            return await ctx.reply(embed=blacklisted_emb, mention_author=False)
        else:
            embed_list: List[BaseEmbed] = []
            while blacklisted:
                blacklisted_embs = BaseEmbed(
                    title=f"\U0001f4dc {ctx.author}'s Block List",
                    description="".join(blacklisted[:3]),
                    colour=self.bot.colour,
                )
                blacklisted = blacklisted[3:]
                blacklisted_embs.set_thumbnail(url=ctx.author.display_avatar.url)
                embed_list.append(blacklisted_embs)
            return await Paginator(self.bot, ctx, embeds=embed_list).send(ctx)

    @highlight.command(
        name="blocked-review",
        brief="Staff review of highlight blocks",
        with_app_command=True,
    )
    @commands.has_permissions(manage_guild=True)
    async def highlight_blocked_review(self, ctx: BaseContext):
        """Surface an overview of highlight block relationships for staff."""

        blocked_entries = await self.bot.db.fetch(
            "SELECT * FROM highlight_blocked WHERE guild_id = $1",
            ctx.guild.id,
        )
        if not blocked_entries:
            return await ctx.reply(
                "No highlight blocks are recorded for this server right now."
            )

        aggregates: Dict[int, List[int]] = {}
        for entry in blocked_entries:
            aggregates.setdefault(entry["user_id"], []).append(entry["object_id"])

        lines: List[str] = []
        for user_id, objects in aggregates.items():
            member = ctx.guild.get_member(user_id)
            if member is None:
                continue
            lines.append(
                f"**{member}** → {len(objects)} block{'s' if len(objects) != 1 else ''}"
            )

        review_embed = BaseEmbed(
            title="Highlight Block Overview",
            description="\n".join(lines[:15]) or "No active data to display.",
            colour=self.bot.colour,
        )
        review_embed.set_footer(
            text="Use highlight blocked-dashboard for an interactive view."
        )
        if getattr(ctx, "interaction", None):
            await ctx.reply(embed=review_embed, ephemeral=True)
        else:
            await ctx.reply(embed=review_embed)

    @highlight.command(
        name="blocked-dashboard",
        brief="Interactive highlight block dashboard",
        with_app_command=True,
    )
    @commands.has_permissions(manage_guild=True)
    async def highlight_blocked_dashboard(self, ctx: BaseContext):
        """Launch an interactive dashboard for highlight blocks."""

        blocked_map = self.bot.highlight_blocked.get(ctx.guild.id)
        if not blocked_map:
            return await ctx.reply("There are no highlight blocks cached right now.")

        view = HighlightBlockDashboard(self.bot, ctx.guild, blocked_map)
        await view.start(ctx)

    @highlight.command(
        name="blocked-audit",
        brief="Audit log for highlight moderation",
        with_app_command=True,
    )
    @commands.has_permissions(manage_guild=True)
    async def highlight_blocked_audit(self, ctx: BaseContext):
        """Display recent highlight block and unblock events to staff."""

        try:
            records = await self.bot.db.fetch(
                "SELECT * FROM highlight_audit WHERE guild_id = $1 ORDER BY occurred_at DESC LIMIT 10",
                ctx.guild.id,
            )
        except asyncpg.UndefinedTableError:
            return await ctx.reply(
                "No audit history is available yet. The audit table will be created automatically after the next action."
            )

        if not records:
            return await ctx.reply("No recent highlight moderation events found.")

        lines = []
        for entry in records:
            timestamp = entry.get("occurred_at")
            lines.append(
                (
                    f"> {self.bot.timestamp(timestamp, style='R') if timestamp else 'Recently'} — "
                    f"<@{entry['actor_id']}> {entry['action']}ed <@{entry['target_id']}> (scope: {entry['scope']})"
                )
            )

        audit_embed = BaseEmbed(
            title="Highlight Audit Trail",
            description="\n".join(lines),
            colour=self.bot.colour,
        )
        if getattr(ctx, "interaction", None):
            await ctx.reply(embed=audit_embed, ephemeral=True)
        else:
            await ctx.reply(embed=audit_embed)
