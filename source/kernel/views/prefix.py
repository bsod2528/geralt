import io
import aiohttp
import discord
import traceback

from discord.errors import NotFound

from ..subclasses.bot import Geralt, CONFIG
from ..subclasses.context import GeraltContext


async def modal_error(self, interaction: discord.Interaction, error: Exception) -> None:
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


class AddPrefix(discord.ui.Modal, title="Add a Prefix"):
    def __init__(self, bot: Geralt, ctx: GeraltContext):
        super().__init__()
        self.bot: Geralt = bot
        self.ctx: GeraltContext = ctx

    prefix = discord.ui.TextInput(
        label="Prefix",
        style=discord.TextStyle.short,
        required=True,
        placeholder="Enter a prefix to add")

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            fetched_data = await self.bot.db.fetch("SELECT UNNEST(guild_prefix) FROM prefix WHERE guild_id = $1", interaction.guild.id)
            for present_prefixes in fetched_data:
                if self.prefix.value.strip() in str(present_prefixes):
                    return await interaction.response.send_message(content=f"`{self.prefix.value.strip()}` ─ is already present in for **{interaction.guild.name}** <:EyesGoBrr:965662700627710032> Please try another one <:WorryPray:941747031356104734>", ephemeral=True)
            query = "INSERT INTO prefix VALUES ($1, ARRAY [$2, '.g']) ON CONFLICT (guild_id) " \
                    "DO UPDATE SET guild_prefix = ARRAY_APPEND(prefix.guild_prefix, $2) WHERE prefix.guild_id = $1"
            await self.bot.db.execute(query, interaction.guild.id, self.prefix.value.strip())
            data = await self.bot.db.fetch("SELECT guild_id, guild_prefix FROM prefix")
            for guild_id, prefixes in data:
                self.bot.prefixes[guild_id] = set(prefixes)
            await interaction.response.send_message(content=f"**{interaction.user}** - `{self.prefix.value.strip()}` has been added to my prefix list for **{interaction.guild.name}** <:SarahLaugh:907109900952420373>", ephemeral=True)
        except Exception as error:
            return await interaction.response.send_message(content=f"```py\{error}\n```", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception, /) -> None:
        await modal_error(error)


class RemovePrefix(discord.ui.Modal, title="Remove a Prefix"):
    def __init__(self, bot: Geralt, ctx: GeraltContext):
        super().__init__()
        self.bot: Geralt = bot
        self.ctx: GeraltContext = ctx

    prefix = discord.ui.TextInput(
        label="Prefix",
        style=discord.TextStyle.short,
        required=True,
        placeholder="Enter a prefix to add")

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            query = "UPDATE prefix SET guild_prefix = ARRAY_REMOVE(prefix.guild_prefix, $2) WHERE guild_id = $1"
            await self.bot.db.execute(query, interaction.guild.id, self.prefix.value.strip())
            data = await self.bot.db.fetch("SELECT guild_id, guild_prefix FROM prefix")
            for guild_id, prefixes in data:
                self.bot.prefixes[guild_id] = set(prefixes)
            return await interaction.response.send_message(content=f"`{self.prefix.value.strip()}` ─ Has been removed from my prefix list for **{interaction.guild.name}** <:SarahLaugh:907109900952420373>", ephemeral=True)
        except Exception as error:
            return await interaction.response.send_message(content=f"```py\n{error}\n```", ephemeral=True)
    async def on_error(self, interaction: discord.Interaction, error: Exception, /) -> None:
        await modal_error(error)


class Prefix(discord.ui.View):
    def __init__(self, bot: Geralt, ctx: GeraltContext):
        super().__init__(timeout=100)
        self.bot: Geralt = bot
        self.ctx: GeraltContext = ctx

    @discord.ui.button(label="Add Prefix",
                       style=discord.ButtonStyle.green)
    async def add_prefix(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddPrefix(self.bot, self.ctx))

    @discord.ui.button(label="Remove Prefix",
                       style=discord.ButtonStyle.red)
    async def remove_prefix(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RemovePrefix(self.bot, self.ctx))

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
