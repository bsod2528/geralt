import datetime
import io
import traceback
from typing import Mapping, Optional

import aiohttp
import discord
import humanize
from dateutil import parser as date_parser
from discord.errors import NotFound

from ...bot import CONFIG, BaseBot
from ...context import BaseContext
from ...embed import BaseEmbed


TODO_STATUSES: tuple[str, ...] = (
    "pending",
    "in_progress",
    "blocked",
    "snoozed",
    "overdue",
    "completed",
    "cancelled",
)

PRIORITY_LABELS = {
    1: "Low",
    2: "Medium",
    3: "High",
    4: "Urgent",
    5: "Critical",
}


def clamp_priority(value: int) -> int:
    return max(1, min(5, value))


def coerce_datetime(value: Optional[str]) -> Optional[datetime.datetime]:
    if not value:
        return None
    parsed = date_parser.parse(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.timezone.utc)
    return parsed.astimezone(datetime.timezone.utc)


def format_dt(dt: Optional[datetime.datetime], *, include_countdown: bool = True) -> str:
    if dt is None:
        return "Not set"
    absolute = discord.utils.format_dt(dt, style="F")
    if include_countdown:
        relation = discord.utils.format_dt(dt, style="R")
        delta = dt - discord.utils.utcnow()
        positive_delta = delta if delta.total_seconds() >= 0 else -delta
        human = humanize.naturaldelta(positive_delta)
        if delta.total_seconds() >= 0:
            return f"{absolute}\nDue in {human} ({relation})"
        return f"{absolute}\nOverdue by {human} ({relation})"
    return absolute


def format_status(status: Optional[str]) -> str:
    if not status:
        return "Pending"
    return status.replace("_", " ").title()


def format_priority(priority: Optional[int]) -> str:
    if priority is None:
        return PRIORITY_LABELS[2]
    return PRIORITY_LABELS.get(int(priority), PRIORITY_LABELS[2])


def build_task_embed(
    bot: BaseBot, ctx: BaseContext, task: Mapping[str, object]
) -> BaseEmbed:
    created_at = task.get("created_at")
    due_at = task.get("due_at")
    remind_at = task.get("remind_at")
    priority = task.get("priority")
    status = task.get("status")

    embed = BaseEmbed(
        title=f"\U0001f4dc {ctx.author}'s Task Info",
        description=(
            f"<:ReplyContinued:930634770004725821> **Task ID** : `{task['task_id']}`\n"
            f"<:ReplyContinued:930634770004725821> **Jump Url** : "
            f"{('[**Click Here**](' + task['jump_url'] + ')') if task['jump_url'] else 'Not available'}\n"
            f"<:Reply:930634822865547294> **Noted On** : {discord.utils.format_dt(created_at, style='F') if created_at else 'Unknown'}\n────"
        ),
        colour=bot.colour,
    )
    embed.add_field(name="Task", value=f">>> {task['task']}", inline=False)
    embed.add_field(name="Status", value=format_status(status))
    embed.add_field(name="Priority", value=format_priority(priority))
    embed.add_field(name="Due", value=format_dt(due_at), inline=False)
    embed.add_field(name="Remind", value=format_dt(remind_at), inline=False)
    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    embed.set_footer(text=f"Run {ctx.clean_prefix}todo for more help")
    return embed


class EditTask(discord.ui.Modal, title="Edit Your Task"):
    edited_task = discord.ui.TextInput(
        label="Task Description",
        required=True,
        style=discord.TextStyle.paragraph,
        placeholder="Describe the task",
        max_length=500,
    )
    due_at_input = discord.ui.TextInput(
        label="Due at (UTC)",
        required=False,
        style=discord.TextStyle.short,
        placeholder="YYYY-MM-DD HH:MM or leave blank",
    )
    remind_at_input = discord.ui.TextInput(
        label="Remind at (UTC)",
        required=False,
        style=discord.TextStyle.short,
        placeholder="Optional reminder time",
    )
    priority_input = discord.ui.TextInput(
        label="Priority (1-5)",
        required=False,
        style=discord.TextStyle.short,
        placeholder="Default is 2 (Medium)",
    )
    status_input = discord.ui.TextInput(
        label="Status",
        required=False,
        style=discord.TextStyle.short,
        placeholder="pending/in_progress/blocked/snoozed/completed",
    )

    def __init__(
        self,
        bot: BaseBot,
        ctx: BaseContext,
        task_id: int,
        *,
        parent_view: "SeeTask",
        task_data: Mapping[str, object],
    ) -> None:
        super().__init__()
        self.bot = bot
        self.ctx = ctx
        self.task_id = task_id
        self.parent_view = parent_view

        self.edited_task.default = str(task_data.get("task", ""))

        due_at = task_data.get("due_at")
        if isinstance(due_at, datetime.datetime):
            self.due_at_input.default = due_at.strftime("%Y-%m-%d %H:%M")

        remind_at = task_data.get("remind_at")
        if isinstance(remind_at, datetime.datetime):
            self.remind_at_input.default = remind_at.strftime("%Y-%m-%d %H:%M")

        priority = task_data.get("priority")
        if priority is not None:
            self.priority_input.default = str(priority)

        status = task_data.get("status")
        if status:
            self.status_input.default = str(status)

    async def on_submit(self, interaction: discord.Interaction, /) -> None:
        errors: list[str] = []

        cleaned_task = self.edited_task.value.strip()
        if not cleaned_task:
            errors.append("Task description cannot be empty.")

        try:
            due_at = coerce_datetime(self.due_at_input.value.strip())
        except Exception:
            errors.append("Unable to parse the due date. Use formats like 2025-01-31 14:30.")
            due_at = None

        try:
            remind_at = coerce_datetime(self.remind_at_input.value.strip())
        except Exception:
            errors.append("Unable to parse the reminder time. Use formats like 2025-01-31 13:30.")
            remind_at = None

        priority_value = 2
        if self.priority_input.value:
            try:
                priority_value = clamp_priority(int(self.priority_input.value))
            except ValueError:
                errors.append("Priority must be an integer between 1 and 5.")

        status_value = self.status_input.value.strip().lower() if self.status_input.value else "pending"
        if status_value and status_value not in TODO_STATUSES:
            valid_statuses = ", ".join(TODO_STATUSES)
            errors.append(f"Status must be one of: {valid_statuses}.")

        if due_at and remind_at and remind_at > due_at:
            errors.append("Reminder time must be before the due time.")

        if errors:
            await interaction.response.send_message("\n".join(errors), ephemeral=True)
            return

        message = getattr(self.ctx, "message", None)
        created_at = getattr(message, "created_at", discord.utils.utcnow())
        jump_url = getattr(message, "jump_url", None)

        await self.bot.db.execute(
            """
            UPDATE todo
               SET task = $1,
                   jump_url = $2,
                   created_at = $3,
                   due_at = $4,
                   remind_at = $5,
                   priority = $6,
                   status = $7
             WHERE task_id = $8
               AND user_id = $9
            """,
            cleaned_task,
            jump_url,
            created_at,
            due_at,
            remind_at,
            priority_value,
            status_value or "pending",
            self.task_id,
            self.ctx.author.id,
        )

        await self.parent_view.refresh_message()

        task_edited_emb = BaseEmbed(
            title="\U0001f91d Task Updated",
            description=(
                f"<:ReplyContinued:930634770004725821> **Task ID** : `{self.task_id}`\n"
                f"<:Reply:930634822865547294> **Edited On** : {self.bot.timestamp(created_at, style='F')}\n────"
            ),
            colour=self.bot.colour,
        )
        task_edited_emb.add_field(name="Task", value=f">>> {cleaned_task}")
        task_edited_emb.add_field(name="Due", value=format_dt(due_at))
        task_edited_emb.add_field(name="Remind", value=format_dt(remind_at))
        task_edited_emb.add_field(name="Priority", value=format_priority(priority_value))
        task_edited_emb.add_field(name="Status", value=format_status(status_value))
        task_edited_emb.set_thumbnail(url=interaction.user.display_avatar.url)
        task_edited_emb.set_footer(text=f"Run {self.ctx.clean_prefix}todo for more help")

        await interaction.response.send_message(embed=task_edited_emb, ephemeral=True)

    async def on_error(
        self, interaction: discord.Interaction, error: Exception, /
    ) -> None:
        async with aiohttp.ClientSession() as session:
            modal_webhook = discord.Webhook.partial(
                id=CONFIG.get("ERROR_ID"),
                token=CONFIG.get("ERROR_TOKEN"),
                session=session,
            )
            data = "".join(
                traceback.format_exception(type(error), error, error.__traceback__)
            )
            try:
                await modal_webhook.send(
                    content=f"```py\n{data}\n```\n|| Break Point ||"
                )
            except (discord.HTTPException, discord.Forbidden):
                await modal_webhook.send(
                    file=discord.File(io.StringIO(data), filename="Traceback.py")
                )
                await modal_webhook.send(content="|| Break Point ||")
            await session.close()


class SeeTask(discord.ui.View):
    STATUS_CYCLE: tuple[str, ...] = (
        "pending",
        "in_progress",
        "blocked",
        "snoozed",
        "completed",
    )

    def __init__(
        self,
        bot: BaseBot,
        ctx: BaseContext,
        task_id: int,
        *,
        task_data: Mapping[str, object],
    ):
        super().__init__(timeout=100)
        self.bot = bot
        self.ctx = ctx
        self.task_id = task_id
        self.task_data = task_data
        self.message: Optional[discord.Message] = None

        self.update_button_state()

    def update_button_state(self) -> None:
        status = str(self.task_data.get("status") or "pending").lower()
        if hasattr(self, "status_toggle"):
            self.status_toggle.label = f"Status: {format_status(status)}"
        if hasattr(self, "complete_task"):
            self.complete_task.disabled = status == "completed"

    async def refresh_message(self) -> bool:
        record = await self.bot.db.fetchrow(
            "SELECT * FROM todo WHERE task_id = $1 AND user_id = $2",
            self.task_id,
            self.ctx.author.id,
        )
        if record is None:
            await self.disable_all(reason="Task removed")
            return False
        self.task_data = dict(record)
        self.update_button_state()
        if self.message:
            await self.message.edit(
                content=None,
                embed=build_task_embed(self.bot, self.ctx, record),
                view=self,
            )
        return True

    async def disable_all(self, *, reason: Optional[str] = None) -> None:
        for child in self.children:
            child.disabled = True
        if self.message:
            await self.message.edit(content=reason, embed=None, view=self)
        self.stop()

    async def send_modal(self, interaction: discord.Interaction) -> None:
        record = await self.bot.db.fetchrow(
            "SELECT * FROM todo WHERE task_id = $1 AND user_id = $2",
            self.task_id,
            self.ctx.author.id,
        )
        if record is None:
            await interaction.response.send_message(
                "This task no longer exists.", ephemeral=True
            )
            await self.disable_all(reason="Task removed")
            return
        modal = EditTask(
            self.bot,
            self.ctx,
            self.task_id,
            parent_view=self,
            task_data=dict(record),
        )
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Edit Task", style=discord.ButtonStyle.grey)
    async def edit_task(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        try:
            await self.send_modal(interaction)
        except Exception as error:
            await interaction.response.send_message(str(error), ephemeral=True)

    @discord.ui.button(label="Status", style=discord.ButtonStyle.blurple)
    async def status_toggle(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        current_status = str(self.task_data.get("status") or "pending").lower()
        try:
            index = self.STATUS_CYCLE.index(current_status)
        except ValueError:
            index = 0
        next_status = self.STATUS_CYCLE[(index + 1) % len(self.STATUS_CYCLE)]
        await self.bot.db.execute(
            "UPDATE todo SET status = $1 WHERE task_id = $2 AND user_id = $3",
            next_status,
            self.task_id,
            self.ctx.author.id,
        )
        updated = await self.refresh_message()
        message = f"Status updated to **{format_status(next_status)}**."
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        elif updated:
            await interaction.response.send_message(message, ephemeral=True)
        else:
            await interaction.response.send_message(
                "This task no longer exists.", ephemeral=True
            )

    @discord.ui.button(label="Complete", style=discord.ButtonStyle.green)
    async def complete_task(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await self.bot.db.execute(
            "UPDATE todo SET status = 'completed', remind_at = NULL WHERE task_id = $1 AND user_id = $2",
            self.task_id,
            self.ctx.author.id,
        )
        updated = await self.refresh_message()
        content = (
            f"Successfully marked Task ID `{self.task_id}` as completed <:RavenPray:914410353155244073>"
        )
        if interaction.response.is_done():
            await interaction.followup.send(content, ephemeral=True)
        elif updated:
            await interaction.response.send_message(content, ephemeral=True)
        else:
            await interaction.response.send_message(
                "This task no longer exists.", ephemeral=True
            )

    async def snooze(self, interaction: discord.Interaction, delta: datetime.timedelta) -> None:
        now = discord.utils.utcnow()
        remind_at = now + delta
        due_at = self.task_data.get("due_at")
        if isinstance(due_at, datetime.datetime) and remind_at > due_at:
            remind_at = due_at
        await self.bot.db.execute(
            "UPDATE todo SET remind_at = $1, status = 'snoozed' WHERE task_id = $2 AND user_id = $3",
            remind_at,
            self.task_id,
            self.ctx.author.id,
        )
        updated = await self.refresh_message()
        message = f"Snoozed task for {humanize.precisedelta(delta, minimum_unit='minutes')}"
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        elif updated:
            await interaction.response.send_message(message, ephemeral=True)
        else:
            await interaction.response.send_message(
                "This task no longer exists.", ephemeral=True
            )

    @discord.ui.button(label="Snooze 30m", style=discord.ButtonStyle.gray)
    async def snooze_30(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await self.snooze(interaction, datetime.timedelta(minutes=30))

    @discord.ui.button(label="Snooze 2h", style=discord.ButtonStyle.gray)
    async def snooze_2h(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await self.snooze(interaction, datetime.timedelta(hours=2))

    @discord.ui.button(label="Delete Task", style=discord.ButtonStyle.red)
    async def delete_task(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await self.bot.db.execute(
            "DELETE FROM todo WHERE task_id = $1 AND user_id = $2",
            self.task_id,
            self.ctx.author.id,
        )
        await self.disable_all(
            reason=(
                f"Successfully deleted Task ID `{self.task_id}` from your todo list <:RavenPray:914410353155244073>"
            )
        )
        if interaction.response.is_done():
            await interaction.followup.send("Task deleted.", ephemeral=True)
        else:
            await interaction.response.send_message(
                "Task deleted.", ephemeral=True
            )

    async def on_timeout(self) -> None:
        await self.disable_all()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        pain = (
            f"This view can't be handled by you at the moment, invoke for yourself by running "
            f"`{self.ctx.clean_prefix}{self.ctx.command}` for the `{self.ctx.command}` command <:SarahPray:920484222421045258>"
        )
        if interaction.user != self.ctx.author:
            try:
                await interaction.response.send_message(
                    content=pain, ephemeral=True
                )
            except NotFound:
                pass
            return False
        return True
