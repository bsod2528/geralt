"""Persistent moderation case management utilities."""

from __future__ import annotations

import csv
import datetime
import io
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

import discord

from ...bot import BaseBot
from ...context import BaseContext
from ...embed import BaseEmbed


@dataclass
class ModerationCase:
    """Data container representing a single moderation case entry."""

    case_id: int
    guild_id: int
    target_id: int
    actor_id: int
    action_type: str
    reason: Optional[str]
    evidence: List[str]
    expires_at: Optional[datetime.datetime]
    created_at: datetime.datetime
    metadata: Dict[str, Any]

    @property
    def target_mention(self) -> str:
        return f"<@{self.target_id}>"

    @property
    def actor_mention(self) -> str:
        return f"<@{self.actor_id}>"


class CaseManager:
    """Helper responsible for storing and presenting moderation cases."""

    def __init__(self, bot: BaseBot):
        self.bot = bot

    # ------------------------------------------------------------------
    # Table management
    # ------------------------------------------------------------------
    async def ensure_tables(self) -> None:
        """Create the moderation case tables if they are missing."""

        await self.bot.db.execute(
            """
            CREATE TABLE IF NOT EXISTS moderation_cases (
                case_id BIGSERIAL PRIMARY KEY,
                guild_id BIGINT NOT NULL,
                target_id BIGINT NOT NULL,
                actor_id BIGINT NOT NULL,
                action_type TEXT NOT NULL,
                reason TEXT,
                evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
                expires_at TIMESTAMPTZ,
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT (TIMEZONE('UTC', NOW()))
            )
            """
        )
        await self.bot.db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_moderation_cases_guild
                ON moderation_cases (guild_id)
            """
        )
        await self.bot.db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_moderation_cases_target
                ON moderation_cases (guild_id, target_id)
            """
        )

        await self.bot.db.execute(
            """
            CREATE TABLE IF NOT EXISTS moderation_case_settings (
                guild_id BIGINT PRIMARY KEY,
                summary_channel_id BIGINT,
                last_summary_at TIMESTAMPTZ
            )
            """
        )

        await self.bot.db.execute(
            """
            CREATE TABLE IF NOT EXISTS moderation_case_summaries (
                summary_id BIGSERIAL PRIMARY KEY,
                guild_id BIGINT NOT NULL,
                period_start TIMESTAMPTZ NOT NULL,
                period_end TIMESTAMPTZ NOT NULL,
                generated_at TIMESTAMPTZ NOT NULL DEFAULT (TIMEZONE('UTC', NOW())),
                summary JSONB NOT NULL
            )
            """
        )
        await self.bot.db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_moderation_case_summaries_guild
                ON moderation_case_summaries (guild_id, generated_at)
            """
        )

    # ------------------------------------------------------------------
    # Case persistence helpers
    # ------------------------------------------------------------------
    async def log_case(
        self,
        guild: discord.Guild,
        target: discord.abc.Snowflake,
        actor: discord.abc.Snowflake,
        action: str,
        *,
        reason: Optional[str] = None,
        evidence: Optional[Iterable[str]] = None,
        expires_at: Optional[datetime.datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ModerationCase:
        """Persist a moderation action and return the stored case."""

        attachments = self._normalise_evidence(evidence)
        metadata = metadata or {}
        record = await self.bot.db.fetchrow(
            """
            INSERT INTO moderation_cases (
                guild_id,
                target_id,
                actor_id,
                action_type,
                reason,
                evidence,
                expires_at,
                metadata
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING *
            """,
            guild.id,
            target.id,
            actor.id,
            action,
            reason,
            attachments,
            expires_at,
            metadata,
        )
        return self._record_to_case(record)

    async def fetch_case(
        self, guild_id: int, case_id: int
    ) -> Optional[ModerationCase]:
        record = await self.bot.db.fetchrow(
            """
            SELECT * FROM moderation_cases
            WHERE guild_id = $1 AND case_id = $2
            """,
            guild_id,
            case_id,
        )
        if record is None:
            return None
        return self._record_to_case(record)

    async def append_appeal(
        self,
        case: ModerationCase,
        author: discord.abc.Snowflake,
        reason: str,
        evidence: Optional[Iterable[str]] = None,
    ) -> Tuple[ModerationCase, Dict[str, Any]]:
        """Attach an appeal entry to a case and persist it."""

        metadata = dict(case.metadata)
        appeals: List[Dict[str, Any]] = list(metadata.get("appeals", []))
        payload = {
            "author_id": author.id,
            "reason": reason,
            "submitted_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "evidence": self._normalise_evidence(evidence),
        }
        appeals.append(payload)
        metadata["appeals"] = appeals
        record = await self.bot.db.fetchrow(
            """
            UPDATE moderation_cases
            SET metadata = $1
            WHERE case_id = $2
            RETURNING *
            """,
            metadata,
            case.case_id,
        )
        return self._record_to_case(record), payload

    async def export_cases(
        self, guild_id: int, *, target_id: Optional[int] = None
    ) -> Optional[discord.File]:
        """Export cases to a CSV file for archival or auditing."""

        if target_id is not None:
            rows = await self.bot.db.fetch(
                """
                SELECT * FROM moderation_cases
                WHERE guild_id = $1 AND target_id = $2
                ORDER BY created_at ASC
                """,
                guild_id,
                target_id,
            )
        else:
            rows = await self.bot.db.fetch(
                """
                SELECT * FROM moderation_cases
                WHERE guild_id = $1
                ORDER BY created_at ASC
                """,
                guild_id,
            )

        if not rows:
            return None

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "case_id",
                "created_at",
                "action_type",
                "target_id",
                "actor_id",
                "reason",
                "evidence",
                "expires_at",
            ]
        )

        for row in rows:
            writer.writerow(
                [
                    row["case_id"],
                    row["created_at"].isoformat() if row["created_at"] else None,
                    row["action_type"],
                    row["target_id"],
                    row["actor_id"],
                    row["reason"],
                    "; ".join(row["evidence"] or []),
                    row["expires_at"].isoformat() if row["expires_at"] else None,
                ]
            )

        data = buffer.getvalue().encode()
        buffer.close()
        filename = (
            f"moderation-cases-{guild_id}-{target_id}.csv"
            if target_id
            else f"moderation-cases-{guild_id}.csv"
        )
        return discord.File(io.BytesIO(data), filename=filename)

    # ------------------------------------------------------------------
    # Summary helpers
    # ------------------------------------------------------------------
    async def dispatch_weekly_summaries(self) -> None:
        """Generate and dispatch weekly summaries where configured."""

        now = datetime.datetime.now(datetime.timezone.utc)
        default_period_start = now - datetime.timedelta(days=7)

        settings_rows = await self.bot.db.fetch(
            """
            SELECT guild_id, summary_channel_id, last_summary_at
            FROM moderation_case_settings
            WHERE summary_channel_id IS NOT NULL
            """
        )

        for settings in settings_rows:
            last_sent: Optional[datetime.datetime] = settings["last_summary_at"]
            if last_sent and (now - last_sent) < datetime.timedelta(days=7):
                continue

            guild_id: int = settings["guild_id"]
            period_start = last_sent or default_period_start
            if period_start < default_period_start:
                period_start = default_period_start
            summary_rows = await self.bot.db.fetch(
                """
                SELECT action_type, COUNT(*) AS total
                FROM moderation_cases
                WHERE guild_id = $1
                  AND created_at >= $2
                  AND created_at < $3
                GROUP BY action_type
                ORDER BY action_type
                """,
                guild_id,
                period_start,
                now,
            )

            summary_data = [
                {"action": row["action_type"], "count": row["total"]}
                for row in summary_rows
            ]

            embed = BaseEmbed(
                title="Weekly Moderation Summary",
                description=(
                    f"Cases recorded between {discord.utils.format_dt(period_start, style='f')} "
                    f"and {discord.utils.format_dt(now, style='f')}"
                ),
                colour=self.bot.colour,
            )
            total_count = sum(row["total"] for row in summary_rows)
            if summary_rows:
                for row in summary_rows:
                    embed.add_field(
                        name=row["action_type"].replace("_", " ").title(),
                        value=f"`{row['total']}` cases",
                        inline=False,
                    )
            else:
                embed.add_field(
                    name="No actions recorded",
                    value="No moderation actions were logged during this window.",
                    inline=False,
                )

            embed.set_footer(text=f"Total actions: {total_count}")

            channel = await self._resolve_channel(settings["summary_channel_id"])
            if channel is not None:
                try:
                    await channel.send(embed=embed)
                except discord.HTTPException:
                    pass

            await self.bot.db.execute(
                """
                INSERT INTO moderation_case_summaries (
                    guild_id,
                    period_start,
                    period_end,
                    summary
                )
                VALUES ($1, $2, $3, $4)
                """,
                guild_id,
                period_start,
                now,
                summary_data,
            )

            await self.bot.db.execute(
                "UPDATE moderation_case_settings SET last_summary_at = $1 WHERE guild_id = $2",
                now,
                guild_id,
            )

    async def set_summary_channel(
        self, guild_id: int, channel_id: Optional[int]
    ) -> None:
        await self.bot.db.execute(
            """
            INSERT INTO moderation_case_settings (guild_id, summary_channel_id, last_summary_at)
            VALUES ($1, $2, NULL)
            ON CONFLICT (guild_id)
            DO UPDATE SET summary_channel_id = EXCLUDED.summary_channel_id
            """,
            guild_id,
            channel_id,
        )

    async def get_summary_channel(
        self, guild_id: int
    ) -> Optional[int]:
        record = await self.bot.db.fetchrow(
            "SELECT summary_channel_id FROM moderation_case_settings WHERE guild_id = $1",
            guild_id,
        )
        if record:
            return record["summary_channel_id"]
        return None

    async def get_summary_destination(
        self, guild_id: int
    ) -> Optional[discord.abc.Messageable]:
        channel_id = await self.get_summary_channel(guild_id)
        if channel_id is None:
            return None
        return await self._resolve_channel(channel_id)

    # ------------------------------------------------------------------
    # Presentation helpers
    # ------------------------------------------------------------------
    def collect_evidence(self, ctx: BaseContext) -> List[str]:
        attachments: List[str] = []
        if ctx.message:
            attachments.extend(att.url for att in ctx.message.attachments)
        interaction = getattr(ctx, "interaction", None)
        if interaction:
            attachments.extend(
                attachment.url for attachment in getattr(interaction, "attachments", [])
            )
        return self._normalise_evidence(attachments)

    def decorate_embed_with_case(
        self, embed: BaseEmbed, case: ModerationCase
    ) -> BaseEmbed:
        """Attach case metadata to an existing embed."""

        embed.set_footer(
            text=(
                f"Case #{case.case_id} • Logged "
                f"{discord.utils.format_dt(case.created_at, style='f')}"
            )
        )
        if case.evidence:
            embed.add_field(
                name="Evidence",
                value="\n".join(case.evidence),
                inline=False,
            )
        if case.expires_at:
            embed.add_field(
                name="Expires",
                value=discord.utils.format_dt(case.expires_at, style="R"),
                inline=False,
            )
        embed.description = (embed.description or "") + (
            f"\n\n**Case ID:** `#{case.case_id}`"
        )
        return embed

    def render_case_embed(
        self,
        guild: discord.Guild,
        case: ModerationCase,
        *,
        include_appeals: bool = True,
    ) -> BaseEmbed:
        embed = BaseEmbed(
            title=f"Case #{case.case_id} — {case.action_type.replace('_', ' ').title()}",
            colour=self.bot.colour,
        )
        embed.add_field(
            name="Target",
            value=f"{case.target_mention} (`{case.target_id}`)",
            inline=False,
        )
        embed.add_field(
            name="Actor",
            value=f"{case.actor_mention} (`{case.actor_id}`)",
            inline=False,
        )
        if case.reason:
            embed.add_field(name="Reason", value=f"```{case.reason}```", inline=False)
        if case.evidence:
            embed.add_field(
                name="Evidence",
                value="\n".join(case.evidence),
                inline=False,
            )
        embed.timestamp = case.created_at
        if case.expires_at:
            embed.add_field(
                name="Expires",
                value=discord.utils.format_dt(case.expires_at, style="F"),
                inline=False,
            )

        if include_appeals and case.metadata.get("appeals"):
            appeals = case.metadata.get("appeals", [])
            formatted = []
            for entry in appeals[-5:]:
                submitted_at = entry.get("submitted_at")
                timestamp = ""
                if submitted_at:
                    try:
                        parsed = datetime.datetime.fromisoformat(submitted_at)
                    except ValueError:
                        parsed = None
                    if parsed:
                        parsed = parsed.replace(tzinfo=datetime.timezone.utc)
                        timestamp = discord.utils.format_dt(parsed, style="R")
                formatted.append(
                    f"<@{entry['author_id']}> — {timestamp}\n{entry['reason']}"
                )
            embed.add_field(
                name="Appeals",
                value="\n\n".join(formatted),
                inline=False,
            )

        embed.set_footer(text=f"Guild ID: {guild.id}")
        return embed

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _normalise_evidence(
        self, evidence: Optional[Iterable[str]]
    ) -> List[str]:
        unique: List[str] = []
        if not evidence:
            return unique
        for item in evidence:
            if item and item not in unique:
                unique.append(item)
        return unique

    async def _resolve_channel(
        self, channel_id: Optional[int]
    ) -> Optional[discord.abc.Messageable]:
        if channel_id is None:
            return None
        channel = self.bot.get_channel(channel_id)
        if channel is not None and isinstance(channel, discord.abc.Messageable):
            return channel
        try:
            fetched = await self.bot.fetch_channel(channel_id)
        except (discord.HTTPException, discord.Forbidden, discord.NotFound):
            return None
        if isinstance(fetched, discord.abc.Messageable):
            return fetched
        return None

    def _record_to_case(self, record: Any) -> ModerationCase:
        return ModerationCase(
            case_id=record["case_id"],
            guild_id=record["guild_id"],
            target_id=record["target_id"],
            actor_id=record["actor_id"],
            action_type=record["action_type"],
            reason=record["reason"],
            evidence=list(record["evidence"] or []),
            expires_at=record["expires_at"],
            created_at=record["created_at"],
            metadata=dict(record["metadata"] or {}),
        )


__all__ = ("CaseManager", "ModerationCase")

