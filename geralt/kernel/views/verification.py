from __future__ import annotations
import io
import traceback
from typing import TYPE_CHECKING

import aiohttp
import discord
import dotenv
from dotenv import dotenv_values

from ...context import BaseContext
from ...embed import BaseEmbed

if TYPE_CHECKING:
    from ...bot import BaseBot

dotenv.load_dotenv()
CONFIG = dotenv_values("config.env")


async def modal_error(error: Exception):
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
        except (discord.HTTPException, discord.Forbidden):
            await modal_webhook.send(file=discord.File(io.StringIO(data), filename="Traceback.py"))
            await modal_webhook.send(content="|| Break Point ||")
        await session.close()


class SetupVerificationModal(discord.ui.Modal, title="Setup Verification"):
    def __init__(
            self,
            bot: BaseBot,
            ctx: BaseContext,
            channel: discord.TextChannel):
        super().__init__()
        self.bot: BaseBot = bot
        self.ctx: BaseContext = ctx
        self.channel = channel

    question = discord.ui.TextInput(
        label="Question",
        required=True,
        placeholder="Your \"Question\" goes here.")

    answer = discord.ui.TextInput(
        label="Answer",
        required=True,
        placeholder="Your \"Answer\" goes here.")

    role_id = discord.ui.TextInput(
        label="ID of the Role",
        required=True,
        placeholder="ID of the role to give.")

    async def on_submit(self, interaction: discord.Interaction) -> None:
        verify_emb = BaseEmbed(
            description=f"Interact with the button below and verify yourself.",
            colour=self.bot.colour)
        verify_emb.add_field(
            name="Question:",
            value=f"> {self.question.value.strip()}")
        verify_emb.add_field(
            name="Answer:",
            value=f"> {self.answer.value.strip()}",
            inline=False)
        try:
            verify_emb.set_author(
                name=f"\U00002728 Verify Yourself in {self.ctx.guild.name}",
                url=self.ctx.guild.icon.url)
        except BaseException:
            verify_emb.set_author(
                name=f"\U00002728 Verify Yourself in {self.ctx.guild.name}")

        verification_sent_message = await self.channel.send(embed=verify_emb, view=VerificationCall(self.bot, self.ctx))

        query = "INSERT INTO verification VALUES ($1, $2, $3, $4, $5, $6)"
        await self.bot.db.execute(query, self.ctx.guild.id, self.question.value.strip(), self.answer.value.strip(), self.role_id.value.strip(), str(self.channel.id), str(verification_sent_message.id))
        self.bot.verification[interaction.guild.id] = [self.question.value.strip(), self.answer.value.strip(
        ), self.role_id.value.strip(), str(self.channel.id), str(verification_sent_message.id)]

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await modal_error(error)


class AnswerVerification(discord.ui.Modal, title="Answer the verification"):
    def __init__(self, bot: BaseBot, ctx: BaseContext):
        super().__init__()
        self.bot: BaseBot = bot
        self.ctx: BaseContext = ctx

    answer = discord.ui.TextInput(
        label="Answer",
        required=True,
        placeholder="Enter the answer.")

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            actual_answer = self.bot.verification[interaction.guild.id][1]
        except KeyError:
            actual_answer = await self.bot.db.fetchval("SELECT answer FROM verification WHERE guild_id = $1", interaction.guild.id)
        if actual_answer != self.answer.value.strip():
            return await interaction.response.send_message(content=f"`{self.answer.value.strip()}` is the incorrect answer. Please check properly and retry.", ephemeral=True)
        if actual_answer == self.answer.value.strip():
            try:
                role = self.bot.verification[interaction.guild.id][2]
            except KeyError:
                role = await self.bot.db.fetchval("SELECT role_id FROM verification WHERE guild_id = $1", interaction.guild.id)
            try:
                await interaction.user.add_roles(discord.Object(role), reason=f"Got verified by {self.bot.user}")
                await interaction.response.send_message(content=f"**{interaction.user}** ─ you have been verified successfuly and got the <@&{role}>", ephemeral=True)
            except discord.errors.Forbidden:
                return await interaction.response.send_message(content=f"Please contact the `{interaction.guild}'s` admin and tell them that <@&{role}> is higher than my role in the role order <a:Grimacing:914905757588283422>", ephemeral=True)
            except discord.HTTPException:
                return await interaction.response.send_message(content=f"**{interaction.user}** ─ an error has occured. Please try again in a while", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await modal_error(error)


class SetupVerification(discord.ui.View):
    def __init__(
            self,
            bot: BaseBot,
            ctx: BaseContext,
            channel: discord.TextChannel):
        super().__init__()
        self.bot: BaseBot = bot
        self.ctx: BaseContext = ctx
        self.channel = channel

        if ctx.interaction:
            self.delete.disabled = True

    @discord.ui.button(label="Setup Verification",
                       style=discord.ButtonStyle.grey,
                       emoji="<a:Owner:905750348457738291>")
    async def setup_verification(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetupVerificationModal(self.bot, self.ctx, self.channel))

    @discord.ui.button(label="Delete",
                       style=discord.ButtonStyle.red,
                       emoji="<a:Trash:906004182463569961>")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()

    async def send(self):
        verification_help_emb = BaseEmbed(
            title="Verification Help",
            description=f"`Question`, `Answer`, and `Role ID` are required to be filled. Set a standard question and answer for users to input.\n\n Get the id of the role by typing `\\` before mentioning the role and then send it. You should be good to go.",
            colour=self.bot.colour)
        self.message = await self.ctx.send(embed=verification_help_emb, view=self)

    async def on_timeout(self) -> None:
        for view in self.children:
            view.disabled = True
        await self.message.edit(view=self)


class VerificationCall(discord.ui.View):
    def __init__(self, bot: BaseBot, ctx: BaseContext):
        super().__init__(timeout=None)
        self.bot: BaseBot = bot
        self.ctx: BaseContext = ctx

    @discord.ui.button(label="Verify Yourself",
                       style=discord.ButtonStyle.grey,
                       emoji="<a:Verify:905748402871095336>",
                       custom_id="call-for-verification")
    async def call_for_verification(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AnswerVerification(self.bot, self.ctx))
