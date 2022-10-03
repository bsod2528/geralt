import io
import aiohttp
import discord
import traceback

from discord.errors import NotFound

from ..views.meta import Confirmation
from ..subclasses.embed import BaseEmbed
from ..subclasses.bot import Geralt, CONFIG
from ..subclasses.context import GeraltContext

class EditTask(discord.ui.Modal, title="Edit Your Task"):
    def __init__(
            self,
            bot: Geralt,
            ctx: GeraltContext,
            task_id: int):
        super().__init__()
        self.bot: Geralt = bot
        self.ctx: GeraltContext = ctx
        self.task_id: int = task_id

    edited_task = discord.ui.TextInput(
        label="Edited Task",
        required=True,
        style=discord.TextStyle.paragraph,
        placeholder="Type in your edited task")

    async def on_submit(self, interaction: discord.Interaction, /) -> None:
        await self.bot.db.execute("UPDATE todo SET task = $1, url = $2, task_created_at = $3 WHERE task_id = $4", self.edited_task.value, self.ctx.message.jump_url, self.ctx.message.created_at, self.task_id)
        task_edited_emb = BaseEmbed(
            title="\U0001f91d Task Edited",
            description=f"<:ReplyContinued:930634770004725821> **Task ID** : `{self.task_id}`\n<:Reply:930634822865547294> **Edited On** : {self.bot.timestamp(self.ctx.message.created_at, style='D')}\n────",
            colour=self.bot.colour)
        task_edited_emb.add_field(
            name="Edited Task :",
            value=f">>> {self.edited_task.value}")
        task_edited_emb.set_thumbnail(url=interaction.user.display_avatar.url)
        task_edited_emb.set_footer(text=f"Run {self.ctx.clean_prefix}todo for more help")
        await interaction.response.send_message(embed=task_edited_emb, ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception, /) -> None:
        async with aiohttp.ClientSession() as session:
            modal_webhook = discord.Webhook.partial(
                    id=CONFIG.get("ERROR_ID"),
                    token=CONFIG.get("ERROR_TOKEN"),
                    session=session)
            data = "".join(
                traceback.format_exception(
                    type(error),
                        error,
                        error.__traceback__))
            try:
                await modal_webhook.send(content=f"```py\n{data}\n```\n|| Break Point ||")
            except(discord.HTTPException, discord.Forbidden):
                await modal_webhook.send(file=discord.File(io.StringIO(data), filename="Traceback.py"))
                await modal_webhook.send(content="|| Break Point ||")
            await session.close()

class SeeTask(discord.ui.View):
    def __init__(
            self,
            bot: Geralt,
            ctx: GeraltContext,
            task_id: int):
        super().__init__(timeout=100)
        self.bot: Geralt = bot
        self.ctx: GeraltContext = ctx
        self.task_id: int = task_id

    @discord.ui.button(label="Edit Task",
                       style=discord.ButtonStyle.grey)
    async def edit_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.send_modal(EditTask(self.bot, self.ctx, self.task_id))
        except Exception as e:
            await interaction.response.send_message(content=e, ephemeral=True)

    @discord.ui.button(label="Delete Task",
                       style=discord.ButtonStyle.red)
    async def delete_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.bot.db.execute(f"DELETE FROM todo WHERE task_id = $1", self.task_id)
        button.disabled = True
        return await interaction.response.edit_message(content=f"Successfully deleted Task ID - `{self.task_id}` from your todo list <:RavenPray:914410353155244073>", view=self)

    async def on_timeout(self) -> None:
        for view in self.children:
            view.disabled = True
        return await self.message.edit(view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{self.ctx.clean_prefix}{self.ctx.command}` for the `{self.ctx.command}` command <:SarahPray:920484222421045258>"
        if interaction.user != self.ctx.author:
            try:
                return await interaction.response.send_message(content=f"{pain}", ephemeral=True)
            except NotFound:
                return
        return True
