import contextlib
import io
import typing
import discord
import asyncpg
import aiohttp
import traceback

from ..subclasses.embed import BaseEmbed
from ..subclasses.bot import Geralt, CONFIG
from ..subclasses.context import GeraltContext

class SetupTicketPanel(discord.ui.Modal, title = "Setup Your Panel"):
    def __init__(self, bot: Geralt, ctx: GeraltContext, channel: discord.TextChannel):
        super().__init__(custom_id = "panel-setup-modal")
        self.bot: Geralt = bot
        self.ctx: GeraltContext = ctx
        self.channel = channel

    category_id = discord.ui.TextInput(
        label = "Category ID",
        required = True,
        placeholder = "ID of the Category for operation.")
        
    ticket_emb_description = discord.ui.TextInput(
        label = "Embed Description",
        style = discord.TextStyle.paragraph,
        required = True,
        placeholder = "Description of the embed for the ticket system.") 
        
    async def on_submit(self, interaction: discord.Interaction) -> None:            
        ticket_emb = BaseEmbed(
            description = self.ticket_emb_description.value,
            color = self.bot.colour)
        ticket_emb.set_thumbnail(url = self.ctx.guild.icon.url)
        ticket_emb.set_author(name = f"{self.ctx.guild}'s Ticket Panel")

        try:
            query = "INSERT INTO ticket_init (guild_id, category_id, sent_message_id, sent_channel_id, jump_url, panel_description) VALUES ($1, $2, $3, $4, $5, $6) " \
                    "ON CONFLICT (id, guild_id) " \
                    "DO UPDATE SET category_id = $1, panel_description = $5"
            sent_panel_message = await self.channel.send(embed = ticket_emb, view = CallTicket(self.bot, self.ctx))
            self.bot.ticket_init[self.ctx.guild.id] = [self.category_id.value.strip(), self.channel.id, sent_panel_message.id, sent_panel_message.jump_url, self.ticket_emb_description.value.strip()]
            await self.bot.db.execute(query, self.ctx.guild.id, self.category_id.value.strip(), sent_panel_message.id, self.channel.id, sent_panel_message.jump_url, self.ticket_emb_description.value.strip())
            id = await self.bot.db.fetchval("SELECT id FROM ticket_init WHERE category_id = $1 and sent_message_id = $2", self.category_id.value.strip(), sent_panel_message.id)
            await interaction.response.send_message(content = f"Global ID ─ for ticket system for **{self.ctx.guild}** guild is `{id}`", ephemeral = True)
        except asyncpg.UniqueViolationError:
            content = f"`{self.category_id.value.strip()}` is a value of a category which is already being utilised for taking care of server members tickets." 
            return await interaction.response.send_message(content = content, ephemeral = True)
                                                                
    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        async with aiohttp.ClientSession() as session:
            modal_webhook = discord.Webhook.partial(id = CONFIG.get("ERROR_ID"), token = CONFIG.get("ERROR_TOKEN"), session = session)
            data = "".join(traceback.format_exception(type(error), error, error.__traceback__))
            try:
                await modal_webhook.send(content = f"```py\n{data}\n```\n|| Break Point ||")
            except(discord.HTTPException, discord.Forbidden):
                await modal_webhook.send(file = discord.File(io.StringIO(data), filename = "Traceback.py"))
                await modal_webhook.send(content = "|| Break Point ||")
            await session.close()

class SetupTicketMessage(discord.ui.Modal, title = "Setup Ticket Message"):
    def __init__(self, bot: Geralt, ctx: GeraltContext):
        super().__init__(custom_id = "message-setup-modal")
        self.bot: Geralt = bot
        self.ctx: GeraltContext = ctx
    
    message_description = discord.ui.TextInput(
        label = "Message Description",
        required = True,
        style = discord.TextStyle.paragraph,
        placeholder = "Enter the description of the message.")

    async def on_submit(self, interaction: discord.Interaction) -> None:
        query = "UPDATE ticket_init SET message_description = $1 WHERE guild_id = $2"
        await self.bot.db.execute(query, self.message_description.value.strip(), self.ctx.guild.id)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        async with aiohttp.ClientSession() as session:
            modal_webhook = discord.Webhook.partial(id = CONFIG.get("ERROR_ID"), token = CONFIG.get("ERROR_TOKEN"), session = session)
            data = "".join(traceback.format_exception(type(error), error, error.__traceback__))
            try:
                await modal_webhook.send(content = f"```py\n{data}\n```\n|| Break Point ||")
            except(discord.HTTPException, discord.Forbidden):
                await modal_webhook.send(file = discord.File(io.StringIO(data), filename = "Traceback.py"))
                await modal_webhook.send(content = "|| Break Point ||")
            await session.close()

class TicketSetup(discord.ui.View):
    def __init__(self, bot: Geralt, ctx: GeraltContext, channel: discord.TextChannel):
        super().__init__(timeout = 180)
        self.bot: Geralt = bot
        self.ctx: GeraltContext = ctx
        self.channel = channel
        self.remove_item(self.send_message_setup)

    @discord.ui.button(label = "Panel Setup", style = discord.ButtonStyle.grey, emoji = "<:DiscordStaff:905668211163406387>")
    async def send_panel_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetupTicketPanel(self.bot, self.ctx, self.channel))
        self.remove_item(self.send_help)
        self.remove_item(self.delete)
        self.add_item(self.send_message_setup)
        self.add_item(self.send_help)
        self.add_item(self.delete)
        with contextlib.suppress(discord.errors):
            await interaction.message.edit(view = self)

    @discord.ui.button(label = "Ticket Message Setup", style = discord.ButtonStyle.grey, emoji = "<:AppWindow:987319960059674635>")
    async def send_message_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetupTicketMessage(self.bot, self.ctx))
        self.send_panel_setup.disabled = True
        with contextlib.suppress(discord.errors):
            await interaction.message.edit(view = self)

    @discord.ui.button(label = "Help", style = discord.ButtonStyle.green, emoji = "<a:CoffeeSip:907110027951742996>")
    async def send_help(self, interaction: discord.Interaction, buttom: discord.ui.Button):
        content = "For `Panel Setup` two arguments have to be filled. They are `Category ID` and `Embed Description`\n> ` ─ ` Category ID : ID of the category in which you want the tickets to be opened up.\n> ` ─ ` Embed Description : What you want to be displayed on the embed of the main system.\n────\n" \
                  "For `Ticket Message Setup` one argument has to be filled. It is `Message Description`\n> ` ─ ` Message Description : What message you want the user to see upon them going to their ticket channel."
        await interaction.response.send_message(content = content, ephemeral = True)

    @discord.ui.button(label = "Delete", style = discord.ButtonStyle.red, emoji = "<a:Trash:906004182463569961>")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()

    async def send(self):
        content = f"Fill up the modal and get ur ticket system going good.\n\n>>> Fill out `Panel Setup` first \U00002757\n" \
                  f"` ─ ` Panel Setup : To set where the system should be located in {self.ctx.guild} and what it should state.\n" \
                  f"` ─ ` Ticket Message Setup : To set what I should state once a ticket is opened."
        self.message = await self.ctx.reply(content = content, view = self)
        return self.message
    
    async def on_timeout(self) -> None:
        try:
            for view in self.children:
                view.disabled = True
                await self.message.edit(view = self)
        except discord.errors.NotFound:
            pass

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{self.ctx.clean_prefix}{self.ctx.command}` for the `{self.ctx.command}` command <:SarahPray:920484222421045258>"
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message(content = f"{pain}", ephemeral = True)
        if interaction.user == self.ctx.author:
            return True

class CallTicket(discord.ui.View):
    def __init__(self, bot: Geralt, ctx: GeraltContext):
        super().__init__(timeout = None)
        self.bot: Geralt = bot
        self.ctx: GeraltContext = ctx
        
    @discord.ui.button(label = "Open a ticket", style = discord.ButtonStyle.grey, emoji = "<:Ticket:987172295762149446>", custom_id = "ticket-call-button")
    async def call_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):    
        try:
            fetch_ticket_deets = await self.bot.db.fetch("SELECT * FROM ticket_init WHERE guild_id = $1", interaction.guild.id)
            try:
                category = self.bot.ticket_init[interaction.guild.id][0]
                message_description = [data["message_description"] for data in fetch_ticket_deets]
            except KeyError:
                category = [data["category_id"] for data in fetch_ticket_deets]
                message_description = [data["message_description"] for data in fetch_ticket_deets]
        
            channel_overwrites : typing.Dict = {
                interaction.guild.default_role : discord.PermissionOverwrite(read_messages = False, send_messages = False),
                interaction.user : discord.PermissionOverwrite(read_messages = True, send_messages = True)}

            try:
                user_channel = await interaction.guild.create_text_channel(
                    name = f"{interaction.user} Ticket", 
                    reason = f"As {interaction.user} opened a ticket", 
                    overwrites = channel_overwrites,
                    category = discord.Object(id = "".join(map(str, category))))
                await self.bot.db.execute(f"INSERT INTO ticket_kernel (guild_id, invoker_id, invoked_at) VALUES ($1, $2, $3)", interaction.guild.id, interaction.user.id, interaction.created_at)
                ticket_id = await self.bot.db.fetchval("SELECT ticket_id FROM ticket_kernel WHERE guild_id = $1 AND invoked_at = $2", interaction.guild.id, interaction.created_at)
                self.bot.ticket_kernel[interaction.guild.id] = [ticket_id, interaction.user.id, interaction.created_at]
            except discord.HTTPException as exception:
                return await interaction.response.send_message(content = f"```py\n{exception}\n```", ephemeral = True)

            user_channel_emb = BaseEmbed(
                description = "".join(message_description),
                colour = self.bot.colour)
            user_channel_emb.set_thumbnail(url = interaction.guild.icon.url)
            user_channel_emb.set_footer(text = f"Ticket ID : {ticket_id}")
            user_channel_emb.set_author(name = f"{interaction.user}'s Ticket Channel", icon_url = interaction.user.display_avatar.url)
        
            user_channel = await self.bot.fetch_channel(user_channel.id)
            await user_channel.send(embed = user_channel_emb)
            await interaction.response.send_message(content = f"Created a ticket {user_channel.mention} <:NanoTick:925271358735257651>", ephemeral = True)
        except discord.errors.NotFound:
            pass