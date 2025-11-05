from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Mapping, MutableMapping, Optional

import aiohttp
from aiohttp import web
import discord

if TYPE_CHECKING:
    from ...bot import BaseBot

log = logging.getLogger(__name__)


class DashboardAPI:
    """Expose guild-scoped configuration through a lightweight REST API."""

    def __init__(self, bot: "BaseBot") -> None:
        self.bot = bot
        self.app = web.Application(middlewares=[self._error_middleware])
        self.app["bot"] = bot
        self.app.router.add_get("/health", self.health)
        self.app.router.add_get("/guilds/{guild_id:\\d+}/settings", self.get_settings)
        self.app.router.add_patch("/guilds/{guild_id:\\d+}/settings", self.patch_settings)
        self._runner: Optional[web.AppRunner] = None
        self._site: Optional[web.TCPSite] = None

    # ------------------------------------------------------------------
    # Lifecycle management
    # ------------------------------------------------------------------
    async def start(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        """Start the underlying aiohttp application."""

        if self._runner is not None:
            return

        self._runner = web.AppRunner(self.app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, host=host, port=port)
        await self._site.start()
        log.info("Dashboard API listening on %s:%s", host, port)

    async def stop(self) -> None:
        """Stop the aiohttp application and release bound resources."""

        if self._site is not None:
            await self._site.stop()
            self._site = None

        if self._runner is not None:
            await self._runner.cleanup()
            self._runner = None

    # ------------------------------------------------------------------
    # Middleware and helpers
    # ------------------------------------------------------------------
    @staticmethod
    @web.middleware
    async def _error_middleware(
        request: web.Request, handler
    ) -> web.StreamResponse:  # pragma: no cover - exercised via integration
        try:
            return await handler(request)
        except web.HTTPException:
            raise
        except Exception as exc:  # pragma: no cover - defensive logging
            log.exception("Unhandled API error: %s", exc)
            raise web.HTTPInternalServerError(text="Internal server error") from exc

    async def _authorise(self, request: web.Request, guild_id: int) -> discord.Member:
        """Validate OAuth bearer credentials and guild permissions."""

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.lower().startswith("bearer "):
            raise web.HTTPUnauthorized(text="Bearer token required")

        token = auth_header.split(maxsplit=1)[1]
        oauth_user = await self._fetch_oauth_user(token)
        user_id = int(oauth_user["id"])

        guild = self.bot.get_guild(guild_id)
        if guild is None:
            raise web.HTTPNotFound(text="Guild not found")

        member = guild.get_member(user_id)
        if member is None:
            try:
                member = await guild.fetch_member(user_id)
            except discord.NotFound as exc:
                raise web.HTTPForbidden(text="User is not a member of this guild") from exc

        perms = member.guild_permissions
        if not (perms.manage_guild or perms.administrator):
            raise web.HTTPForbidden(text="Insufficient guild permissions")

        return member

    async def _fetch_oauth_user(self, token: str) -> Mapping[str, Any]:
        """Retrieve the OAuth2 identity payload from Discord."""

        session: aiohttp.ClientSession = self.bot.session
        async with session.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {token}"},
        ) as response:
            if response.status != 200:
                raise web.HTTPUnauthorized(text="Invalid OAuth token")
            return await response.json()

    # ------------------------------------------------------------------
    # Serialisers
    # ------------------------------------------------------------------
    def _snapshot(self, guild_id: int) -> Dict[str, Any]:
        """Produce a serialisable snapshot of the guild configuration."""

        return self.bot.guild_configuration_snapshot(guild_id)

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------
    async def health(self, _: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    async def get_settings(self, request: web.Request) -> web.Response:
        guild_id = int(request.match_info["guild_id"])
        await self._authorise(request, guild_id)
        return web.json_response(self._snapshot(guild_id))

    async def patch_settings(self, request: web.Request) -> web.Response:
        guild_id = int(request.match_info["guild_id"])
        await self._authorise(request, guild_id)
        payload = await request.json()

        if not isinstance(payload, Mapping):
            raise web.HTTPBadRequest(text="JSON object payload required")

        updates = {}
        if "prefixes" in payload:
            updates["prefixes"] = await self._update_prefixes(
                guild_id, payload["prefixes"]
            )
        if "highlight" in payload:
            updates["highlight"] = await self._update_highlight(
                guild_id, payload["highlight"]
            )
        if "highlight_blocked" in payload:
            updates["highlight_blocked"] = await self._update_highlight_blocked(
                guild_id, payload["highlight_blocked"]
            )
        if "ticket_panel" in payload:
            updates["ticket_panel"] = await self._update_ticket_panel(
                guild_id, payload["ticket_panel"]
            )
        if "verification_panel" in payload:
            updates["verification_panel"] = await self._update_verification_panel(
                guild_id, payload["verification_panel"]
            )
        if "flags" in payload:
            updates["flags"] = await self._update_flags(
                guild_id, payload["flags"]
            )

        snapshot = self._snapshot(guild_id)
        snapshot.update(updates)
        return web.json_response(snapshot)

    # ------------------------------------------------------------------
    # Update helpers
    # ------------------------------------------------------------------
    async def _update_prefixes(self, guild_id: int, value: Any) -> List[str]:
        if not isinstance(value, Iterable) or isinstance(value, (str, bytes)):
            raise web.HTTPBadRequest(text="prefixes must be an array of strings")

        processed: List[str] = []
        for prefix in value:
            if not isinstance(prefix, str):
                raise web.HTTPBadRequest(text="prefixes must be strings")
            cleaned = prefix.strip()
            if not cleaned:
                continue
            if cleaned not in processed:
                processed.append(cleaned)

        if ".g" not in processed:
            processed.insert(0, ".g")

        await self.bot.db.execute(
            """
            INSERT INTO prefix (guild_id, prefixes)
            VALUES ($1, $2)
            ON CONFLICT (guild_id)
            DO UPDATE SET prefixes = EXCLUDED.prefixes
            """,
            guild_id,
            processed,
        )

        self.bot.prefixes[guild_id] = set(processed)
        return processed

    async def _update_highlight(self, guild_id: int, value: Any) -> List[Dict[str, Any]]:
        if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
            raise web.HTTPBadRequest(
                text="highlight must be an array of user trigger mappings"
            )

        records: List[tuple[int, int, str, datetime.datetime]] = []
        prepared: Dict[int, List[str]] = {}

        for entry in value:
            if not isinstance(entry, Mapping):
                raise web.HTTPBadRequest(text="highlight entries must be objects")
            try:
                user_id = int(entry["user_id"])
            except (KeyError, ValueError, TypeError):
                raise web.HTTPBadRequest(text="highlight entries require user_id")
            triggers = entry.get("triggers", [])
            if not isinstance(triggers, Iterable) or isinstance(triggers, (str, bytes)):
                raise web.HTTPBadRequest(text="triggers must be an array of strings")

            for trigger in triggers:
                if not isinstance(trigger, str):
                    raise web.HTTPBadRequest(text="triggers must be strings")
                cleaned = trigger.strip().lower()
                if not cleaned:
                    continue
                records.append((user_id, guild_id, cleaned, discord.utils.utcnow()))
                prepared.setdefault(user_id, []).append(cleaned)

        await self.bot.db.execute("DELETE FROM highlight WHERE guild_id = $1", guild_id)
        if records:
            await self.bot.db.executemany(
                "INSERT INTO highlight VALUES ($1, $2, $3, $4)", records
            )

        if prepared:
            guild_cache = self.bot.generate_dict_cache(
                [(guild_id, user_id, trigger) for user_id, triggers in prepared.items() for trigger in triggers]
            )
            self.bot.highlight[guild_id] = guild_cache.get(guild_id, {})
        else:
            self.bot.highlight.pop(guild_id, None)

        return [
            {"user_id": user_id, "triggers": sorted(set(triggers))}
            for user_id, triggers in self.bot.highlight.get(guild_id, {}).items()
        ]

    async def _update_highlight_blocked(
        self, guild_id: int, value: Any
    ) -> List[Dict[str, Any]]:
        if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
            raise web.HTTPBadRequest(
                text="highlight_blocked must be an array of mappings"
            )

        records: List[tuple[int, int, int, str, datetime.datetime]] = []
        prepared: Dict[int, List[int]] = {}

        for entry in value:
            if not isinstance(entry, Mapping):
                raise web.HTTPBadRequest(text="highlight_blocked entries must be objects")
            try:
                user_id = int(entry["user_id"])
                object_ids = entry.get("object_ids", [])
            except (KeyError, ValueError, TypeError):
                raise web.HTTPBadRequest(text="highlight_blocked entries require user_id")
            if not isinstance(object_ids, Iterable) or isinstance(object_ids, (str, bytes)):
                raise web.HTTPBadRequest(text="object_ids must be an array")
            object_type = entry.get("object_type", "member")
            if not isinstance(object_type, str):
                raise web.HTTPBadRequest(text="object_type must be a string")

            for object_id in object_ids:
                try:
                    resolved = int(object_id)
                except (TypeError, ValueError):
                    raise web.HTTPBadRequest(text="object_ids must be integers")
                records.append(
                    (user_id, guild_id, resolved, object_type, discord.utils.utcnow())
                )
                prepared.setdefault(user_id, []).append(resolved)

        await self.bot.db.execute(
            "DELETE FROM highlight_blocked WHERE guild_id = $1", guild_id
        )
        if records:
            await self.bot.db.executemany(
                "INSERT INTO highlight_blocked VALUES ($1, $2, $3, $4, $5)", records
            )

        if prepared:
            guild_cache = self.bot.generate_dict_cache(
                [
                    (guild_id, user_id, object_id)
                    for user_id, object_ids in prepared.items()
                    for object_id in object_ids
                ]
            )
            self.bot.highlight_blocked[guild_id] = guild_cache.get(guild_id, {})
        else:
            self.bot.highlight_blocked.pop(guild_id, None)

        return [
            {"user_id": user_id, "object_ids": sorted({*object_ids})}
            for user_id, object_ids in self.bot.highlight_blocked.get(guild_id, {}).items()
        ]

    async def _update_ticket_panel(
        self, guild_id: int, value: Any
    ) -> Optional[Dict[str, Any]]:
        if value in (None, False):
            await self.bot.db.execute(
                "DELETE FROM ticket_init WHERE guild_id = $1", guild_id
            )
            self.bot.ticket_init.pop(guild_id, None)
            return None

        if not isinstance(value, Mapping):
            raise web.HTTPBadRequest(text="ticket_panel must be an object or null")

        try:
            category_id = str(value["category_id"])
            sent_channel_id = str(value["sent_channel_id"])
            sent_message_id = str(value["sent_message_id"])
            jump_url = str(value.get("jump_url", ""))
            panel_description = str(value.get("panel_description", ""))
        except KeyError as exc:
            raise web.HTTPBadRequest(text=f"ticket_panel missing field: {exc.args[0]}")

        record = await self.bot.db.fetchrow(
            """
            INSERT INTO ticket_init (guild_id, category_id, sent_channel_id, sent_message_id, jump_url, panel_description)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (guild_id)
            DO UPDATE SET
                category_id = EXCLUDED.category_id,
                sent_channel_id = EXCLUDED.sent_channel_id,
                sent_message_id = EXCLUDED.sent_message_id,
                jump_url = EXCLUDED.jump_url,
                panel_description = EXCLUDED.panel_description
            RETURNING id, category_id, sent_channel_id, sent_message_id, jump_url, panel_description
            """,
            guild_id,
            category_id,
            sent_channel_id,
            sent_message_id,
            jump_url,
            panel_description,
        )

        cache_entry = [
            record["category_id"],
            record["sent_channel_id"],
            record["sent_message_id"],
            record["jump_url"],
            record["panel_description"],
            record["id"],
        ]
        self.bot.ticket_init[guild_id] = cache_entry

        return {
            "id": record["id"],
            "category_id": record["category_id"],
            "sent_channel_id": record["sent_channel_id"],
            "sent_message_id": record["sent_message_id"],
            "jump_url": record["jump_url"],
            "panel_description": record["panel_description"],
        }

    async def _update_verification_panel(
        self, guild_id: int, value: Any
    ) -> Optional[Dict[str, Any]]:
        if value in (None, False):
            await self.bot.db.execute(
                "DELETE FROM verification WHERE guild_id = $1", guild_id
            )
            self.bot.verification.pop(guild_id, None)
            return None

        if not isinstance(value, Mapping):
            raise web.HTTPBadRequest(
                text="verification_panel must be an object or null"
            )

        try:
            question = str(value["question"])
            answer = str(value["answer"])
            role_id = str(value["role_id"])
            channel_id = str(value["channel_id"])
            message_id = str(value["message_id"])
        except KeyError as exc:
            raise web.HTTPBadRequest(
                text=f"verification_panel missing field: {exc.args[0]}"
            )

        await self.bot.db.execute(
            """
            INSERT INTO verification (guild_id, question, answer, role_id, channel_id, message_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (guild_id)
            DO UPDATE SET
                question = EXCLUDED.question,
                answer = EXCLUDED.answer,
                role_id = EXCLUDED.role_id,
                channel_id = EXCLUDED.channel_id,
                message_id = EXCLUDED.message_id
            """,
            guild_id,
            question,
            answer,
            role_id,
            channel_id,
            message_id,
        )

        self.bot.verification[guild_id] = [
            question,
            answer,
            role_id,
            channel_id,
            message_id,
        ]

        return {
            "question": question,
            "answer": answer,
            "role_id": role_id,
            "channel_id": channel_id,
            "message_id": message_id,
        }

    async def _update_flags(self, guild_id: int, value: Any) -> Dict[str, bool]:
        if not isinstance(value, Mapping):
            raise web.HTTPBadRequest(text="flags must be an object")

        current: MutableMapping[str, bool] = {
            "convert_url_to_webhook": False,
            "snipe": False,
        }
        current.update(self.bot.settings.get(guild_id, {}))

        for key in ("convert_url_to_webhook", "snipe"):
            if key in value:
                raw = value[key]
                if isinstance(raw, bool):
                    current[key] = raw
                else:
                    raise web.HTTPBadRequest(
                        text=f"{key} must be a boolean value"
                    )

        await self.bot.db.execute(
            """
            INSERT INTO guild_settings (guild_id, convert_url_to_webhook, snipe)
            VALUES ($1, $2, $3)
            ON CONFLICT (guild_id)
            DO UPDATE SET
                convert_url_to_webhook = EXCLUDED.convert_url_to_webhook,
                snipe = EXCLUDED.snipe
            """,
            guild_id,
            current["convert_url_to_webhook"],
            current["snipe"],
        )

        self.bot.settings[guild_id] = dict(current)
        return dict(current)
