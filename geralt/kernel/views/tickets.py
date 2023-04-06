from __future__ import annotations

import io
import traceback
import typing
from typing import TYPE_CHECKING, List

import aiohttp
import asyncpg
import discord
import dotenv
from discord.errors import NotFound
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
            id=CONFIG.get("ERROR_ID"), token=CONFIG.get("ERROR_TOKEN"), session=session
        )
        data = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )
        try:
            await modal_webhook.send(content=f"```py\n{data}\n```\n|| Break Point ||")
        except (discord.HTTPException, discord.Forbidden):
            await modal_webhook.send(
                file=discord.File(io.StringIO(data), filename="Traceback.py")
            )
            await modal_webhook.send(content="|| Break Point ||")
        await session.close()


class SetupTicketPanel(discord.ui.Modal, title="Setup Your Panel"):
    def __init__(self, bot: BaseBot, ctx: BaseContext, channel: discord.TextChannel):
        super().__init__()
        self.bot = bot
        self.ctx = ctx
        self.channel = channel

    category_id = discord.ui.TextInput(
        label="Category ID",
        required=True,
        placeholder="ID of the Category for operation.",
    )

    ticket_emb_description = discord.ui.TextInput(
        label="Embed Description",
        style=discord.TextStyle.paragraph,
        required=True,
        placeholder="Description of the embed for the ticket system.",
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        ticket_emb = BaseEmbed(
            description=self.ticket_emb_description.value, color=self.bot.colour
        )
        ticket_emb.set_author(name=f"{self.ctx.guild}'s Ticket Panel")

        try:
            query = "INSERT INTO ticket_init (guild_id, category_id, sent_message_id, sent_channel_id, jump_url, panel_description) VALUES ($1, $2, $3, $4, $5, $6) "
            sent_panel_message = await self.channel.send(
                embed=ticket_emb, view=CallTicket(self.bot, self.ctx)
            )
            self.bot.ticket_init[self.ctx.guild.id] = [
                self.category_id.value.strip(),
                self.channel.id,
                sent_panel_message.id,
                sent_panel_message.jump_url,
                self.ticket_emb_description.value.strip(),
            ]
            await self.bot.db.execute(
                query,
                self.ctx.guild.id,
                self.category_id.value.strip(),
                sent_panel_message.id,
                self.channel.id,
                sent_panel_message.jump_url,
                self.ticket_emb_description.value.strip(),
            )
        except asyncpg.UniqueViolationError:
            content = f"**{self.ctx.guild}** is already has a ticket system. Please run `{self.ctx.clean_prefix}ticket status` for more information."
            return await interaction.response.send_message(
                content=content, ephemeral=True
            )

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        await modal_error(error)


class TicketSetup(discord.ui.View):
    def __init__(self, bot: BaseBot, ctx: BaseContext, channel: discord.TextChannel):
        super().__init__(timeout=180)
        self.bot = bot
        self.ctx = ctx
        self.channel = channel

        if ctx.interaction:
            self.delete.disabled = True

    @discord.ui.button(
        label="Panel Setup",
        style=discord.ButtonStyle.grey,
        emoji="<:DiscordStaff:905668211163406387>",
    )
    async def send_panel_setup(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(
            SetupTicketPanel(self.bot, self.ctx, self.channel)
        )

    @discord.ui.button(
        label="Help",
        style=discord.ButtonStyle.green,
        emoji="<a:CoffeeSip:907110027951742996>",
    )
    async def send_help(
        self, interaction: discord.Interaction, buttom: discord.ui.Button
    ):
        content = (
            "For `Panel Setup` two arguments have to be filled. They are `Category ID` and `Embed Description`\n> ` ─ ` Category ID : ID of the category in which you want the tickets to be opened up.\n> ` ─ ` Embed Description : What you want to be displayed on the embed of the main system.\n────\n"
            "For `Ticket Message Setup` one argument has to be filled. It is `Message Description`\n> ` ─ ` Message Description : What message you want the user to see upon them going to their ticket channel."
        )
        await interaction.response.send_message(content=content, ephemeral=True)

    @discord.ui.button(
        label="Delete",
        style=discord.ButtonStyle.red,
        emoji="<a:Trash:906004182463569961>",
    )
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()

    async def send(self):
        ticket_setup_emb = BaseEmbed(
            title="Setting up Tickets",
            description=f"{self.ctx.author.mention} - Please follow the steps below:",
            colour=self.bot.colour,
        )
        ticket_setup_emb.add_field(
            name="Steps:",
            value="<:One:989876071052750868> Copy the `ID` of the Category you want ticket channels to be made.\n"
            "<:Two:989876145291948122> Click on `Panel Setup` button below and give in your **Category ID** and the message for opening tickets.\n"
            "<:Three:989876184420610099> Submit the modal and you're good to go!",
        )
        ticket_setup_emb.set_thumbnail(
            url="https://cdn.discordapp.com/emojis/987182220626235482.webp?size=96&quality=lossless"
        )
        self.message = await self.ctx.reply(embed=ticket_setup_emb, view=self)
        return self.message

    async def on_timeout(self) -> None:
        try:
            for view in self.children:
                view.disabled = True
                await self.message.edit(view=self)
        except NotFound:
            return

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{self.ctx.clean_prefix}{self.ctx.command}` for the `{self.ctx.command}` command <:SarahPray:920484222421045258>"
        if interaction.user != self.ctx.author:
            try:
                return await interaction.response.send_message(
                    content=f"{pain}", ephemeral=True
                )
            except NotFound:
                return
        return True


class CallTicket(discord.ui.View):
    """A persistent button for opening a ticket."""

    def __init__(self, bot: BaseBot, ctx: BaseContext):
        super().__init__(timeout=None)
        self.bot = bot
        self.ctx = ctx

    @discord.ui.button(
        label="Open a ticket",
        style=discord.ButtonStyle.grey,
        emoji="<:Ticket:987172295762149446>",
        custom_id="call-ticket",
    )
    async def call_ticket(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        try:
            try:
                category = self.bot.ticket_init[interaction.guild.id][0]
            except KeyError:
                fetch_ticket_deets = await self.bot.db.fetch(
                    "SELECT * FROM ticket_init WHERE guild_id = $1",
                    interaction.guild.id,
                )
                category = [data["category_id"] for data in fetch_ticket_deets]

            channel_overwrites: typing.Dict = {
                interaction.guild.default_role: discord.PermissionOverwrite(
                    read_messages=False, send_messages=False
                ),
                interaction.user: discord.PermissionOverwrite(
                    read_messages=True, send_messages=True
                ),
            }

            try:
                user_channel: discord.TextChannel = (
                    await interaction.guild.create_text_channel(
                        name=f"{interaction.user} Ticket",
                        reason=f"As {interaction.user} opened a ticket",
                        overwrites=channel_overwrites,
                        category=discord.Object(id="".join(map(str, category))),
                    )
                )
                await self.bot.db.execute(
                    f"INSERT INTO ticket_kernel (guild_id, invoker_id, channel_id) VALUES ($1, $2, $3)",
                    interaction.guild.id,
                    interaction.user.id,
                    user_channel.id,
                )
                ticket_id = await self.bot.db.fetchval(
                    "SELECT MAX(ticket_id) FROM ticket_kernel WHERE guild_id = $1",
                    interaction.guild.id,
                )
                ticket_kernel = await self.bot.db.fetch("SELECT * FROM ticket_kernel")
                if ticket_kernel:
                    ticket_kernel_list: List = [
                        (data["guild_id"], data["ticket_id"], data["invoker_id"])
                        for data in ticket_kernel
                    ]
                    self.bot.ticket_kernel = self.bot.generate_dict_cache(
                        ticket_kernel_list
                    )
            except discord.HTTPException as exception:
                return await interaction.response.send_message(
                    content=f"```py\n{exception}\n```", ephemeral=True
                )

            user_channel_emb = BaseEmbed(
                title=f"Ticket ID : {ticket_id}",
                description="Please state your issue.",
                colour=self.bot.colour,
            )
            user_channel_emb.set_thumbnail(url=interaction.guild.icon.url)
            user_channel_emb.set_author(
                name=f"{interaction.user}'s Ticket Channel",
                icon_url=interaction.user.display_avatar.url,
            )

            user_channel = await self.bot.fetch_channel(user_channel.id)
            await user_channel.send(embed=user_channel_emb)
            await interaction.response.send_message(
                content=f"Created a ticket {user_channel.mention} <:NanoTick:925271358735257651>",
                ephemeral=True,
            )
        except Exception as e:
            print(e)
