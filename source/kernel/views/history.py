import discord

from discord.errors import NotFound
from typing import Optional, TYPE_CHECKING

from ...kernel.subclasses.embed import BaseEmbed
from ...kernel.subclasses.context import GeraltContext

if TYPE_CHECKING:
    from ...kernel.subclasses.bot import Geralt


class UserHistory(discord.ui.View):
    def __init__(self, bot: "Geralt", ctx: GeraltContext,
                 user: Optional[discord.User]):
        super().__init__()
        self.bot: "Geralt" = bot
        self.ctx: GeraltContext = ctx
        self.user = user

    @discord.ui.button(label="Username",
                       style=discord.ButtonStyle.grey,
                       emoji="<a:Users:905749451350638652>")
    async def see_username_history(self, interaction: discord.Interaction, button: discord.ui.Button):
        usernames = await self.bot.db.fetch("SELECT username, timestamp FROM username_history WHERE user_id = $1", self.user.id)
        data = [
            f"<:Join:932976724235395072> {deets[0]} ─ ({self.bot.timestamp(deets[1], style = 'R')})" for deets in usernames]
        if not usernames:
            return await interaction.response.send_message(content=f"{self.user.mention} ─ Has no records for changes in usernames logged in <:EyesGoBrr:965662700627710032>. To start logging, run `{self.ctx.clean_prefix}log username`", ephemeral=True)
        username_emb = BaseEmbed(
            description="\n".join(data),
            colour=self.bot.colour)
        username_emb.set_author(
            name=f"\U0001f4dc {self.user}'s Username History",
            icon_url=self.user.display_avatar.url)
        try:
            await interaction.response.send_message(embed=username_emb, ephemeral=True)
        except NotFound:
            return

    @discord.ui.button(label="Discriminator",
                       style=discord.ButtonStyle.grey,
                       emoji="<:Channel:905674680436944906>")
    async def see_discriminator_history(self, interaction: discord.Interaction, button: discord.ui.Button):
        discriminators = await self.bot.db.fetch("SELECT discriminator, timestamp FROM discriminator_history WHERE user_id = $1", self.user.id)
        data = [
            f"<:Join:932976724235395072> {deets[0]} ─ ({self.bot.timestamp(deets[1], style = 'R')})" for deets in discriminators]
        if not discriminators:
            return await interaction.response.send_message(content=f"{self.user.mention} ─ Has no records for changes in discriminator logged in <:EyesGoBrr:965662700627710032>. To start logging, run `{self.ctx.clean_prefix}log discriminator`", ephemeral=True)
        discriminator_emb = BaseEmbed(
            description="\n".join(data),
            colour=self.bot.colour)
        discriminator_emb.set_author(
            name=f"\U0001f4dc {self.user}'s Discriminator History",
            url=self.user.display_avatar)
        try:
            await interaction.response.send_message(embed=discriminator_emb, ephemeral=True)
        except NotFound:
            return

    @discord.ui.button(label="Delete",
                       style=discord.ButtonStyle.danger,
                       emoji="<a:Trash:906004182463569961>")
    async def delete_userhistory_message(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message(content="Nope", ephemeral=True)
        return await interaction.message.delete()


class SelectUserLogEvents(discord.ui.View):
    def __init__(self, bot: "Geralt", ctx: GeraltContext):
        super().__init__()
        self.bot: "Geralt" = bot
        self.ctx: GeraltContext = ctx

    @discord.ui.button(label="Avatar", style=discord.ButtonStyle.blurple)
    async def opt_avatar(self, interaction: discord.Interaction, button: discord.ui.Button):
        query = "INSERT INTO user_settings (user_id, avatar) VALUES ($1, $2) " \
                "ON CONFLICT (user_id) " \
                "DO UPDATE SET avatar = $2"
        data = await self.bot.db.fetchval("SELECT avatar FROM user_settings WHERE user_id = $1", interaction.user.id)
        if data:
            await self.bot.db.execute(query, interaction.user.id, False)
            return await interaction.response.send_message(content=f"**{interaction.user}** ─ Successfully `opted out` from avatar logging <:TokoOkay:898611996163985410>", ephemeral=True)

        await self.bot.db.execute(query, interaction.user.id, True)
        await interaction.response.send_message(content=f"**{interaction.user}** ─ Successfully `opted in` from avatar logging <:DuckThumbsUp:917007413259956254>", ephemeral=True)

    @discord.ui.button(label="Username", style=discord.ButtonStyle.blurple)
    async def opt_username(self, interaction: discord.Interaction, button: discord.ui.Button):
        query = "INSERT INTO user_settings (user_id, username) VALUES ($1, $2) " \
                "ON CONFLICT (user_id) " \
                "DO UPDATE SET username = $2"
        data = await self.bot.db.fetchval("SELECT username FROM user_settings WHERE user_id = $1", interaction.user.id)
        if data:
            await self.bot.db.execute(query, interaction.user.id, False)
            return await interaction.response.send_message(content=f"**{interaction.user}** ─ Successfully `opted out` from username logging <:TokoOkay:898611996163985410>", ephemeral=True)

        await self.bot.db.execute(query, interaction.user.id, True)
        await interaction.response.send_message(content=f"**{interaction.user}** ─ Successfully `opted in` from username logging <:DuckThumbsUp:917007413259956254>", ephemeral=True)

    @discord.ui.button(label="Discriminator",
                       style=discord.ButtonStyle.blurple)
    async def opt_discriminator(self, interaction: discord.Interaction, button: discord.ui.Button):
        query = "INSERT INTO user_settings (user_id, discriminator) VALUES ($1, $2) " \
                "ON CONFLICT (user_id) " \
                "DO UPDATE SET discriminator = $2"
        data = await self.bot.db.fetchval("SELECT discriminator FROM user_settings WHERE user_id = $1", interaction.user.id)
        if data:
            await self.bot.db.execute(query, interaction.user.id, False)
            return await interaction.response.send_message(content=f"**{interaction.user}** ─ Successfully `opted out` from discriminator logging <:TokoOkay:898611996163985410>", ephemeral=True)

        await self.bot.db.execute(query, interaction.user.id, True)
        await interaction.response.send_message(content=f"**{interaction.user}** ─ Successfully `opted in` from discriminator logging <:DuckThumbsUp:917007413259956254>", ephemeral=True)
