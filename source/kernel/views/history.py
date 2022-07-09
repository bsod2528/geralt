import discord

from typing import Any, Optional
from discord.ext import commands

from ...kernel.subclasses.bot import Geralt
from ...kernel.subclasses.embed import BaseEmbed
from ...kernel.subclasses.context import GeraltContext

class UserHistory(discord.ui.View):
    def __init__(self, bot: Geralt, ctx: GeraltContext, user: Optional[discord.User]):
        super().__init__()
        self.bot: Geralt = bot
        self.ctx: GeraltContext = ctx
        self.user = user
    
    @discord.ui.button(label = "Username", style = discord.ButtonStyle.grey, emoji = "<a:Users:905749451350638652>")
    async def see_username_history(self, interaction: discord.Interaction, button: discord.ui.Button):
        usernames = await self.bot.db.fetch("SELECT username, timestamp FROM username_history WHERE user_id = $1", self.user.id)
        data = [f"<:Join:932976724235395072> {deets[0]} ─ ({self.bot.timestamp(deets[1], style = 'R')})" for deets in usernames]
        if not usernames:
            return await interaction.response.send_message(content = f"{self.user.mention} ─ Has no records for changes in usernames logged in <:EyesGoBrr:965662700627710032>. To start logging, run `{self.ctx.clean_prefix}log username`", ephemeral = True)
        username_emb = BaseEmbed(
            description = "\n".join(data),
            colour = self.bot.colour)
        username_emb.set_author(name = f"\U0001f4dc {self.user}'s Username History", icon_url= self.user.display_avatar.url)
        await interaction.response.send_message(embed = username_emb, ephemeral = True)
    
    @discord.ui.button(label = "Discriminator", style = discord.ButtonStyle.grey, emoji = "<:Channel:905674680436944906>")
    async def see_discriminator_history(self, interaction: discord.Interaction, button: discord.ui.Button):
        discriminators = await self.bot.db.fetch("SELECT discriminator, timestamp FROM discriminator_history WHERE user_id = $1", self.user.id)
        data = [f"<:Join:932976724235395072> {deets[0]} ─ ({self.bot.timestamp(deets[1], style = 'R')})" for deets in discriminators]
        if not discriminators:
            return await interaction.response.send_message(content = f"{self.user.mention} ─ Has no records for changes in discriminator logged in <:EyesGoBrr:965662700627710032>. To start logging, run `{self.ctx.clean_prefix}log discriminator`", ephemeral = True)
        discriminator_emb = BaseEmbed(
            description = "\n".join(data),
            colour = self.bot.colour)
        discriminator_emb.set_author(name = f"\U0001f4dc {self.user}'s Discriminator History", url = self.user.display_avatar)
        await interaction.response.send_message(embed = discriminator_emb, ephemeral = True)

class SelectUserLogEvents(discord.ui.Select):
    def __init__(self, bot: Geralt, ctx: GeraltContext):
        options = [discord.SelectOption(label = "Avatar", description = "Log your avatars.", emoji = "<a:Click:973748305416835102>", value = "avatar"),
                   discord.SelectOption(label = "Username", description = "Log your usernames.", emoji = "<a:PandaNote:961260552435413052>", value = "username"),
                   discord.SelectOption(label = "Discriminator", description = "Log your discriminators.", emoji = "<:One:989876071052750868> ", value = "discriminator")]
        super().__init__(
            options = options,
            min_values = 1,
            max_values = 3,
            placeholder = "Select the Events you want to log.")
        self.bot: Geralt = bot
        self.ctx: GeraltContext = ctx
        
    async def callback(self, interaction: discord.Interaction) -> Any:
        if self.values[0] == "avatar":
            avatar = "INSERT INTO user_settings (user_id, avatar) VALUES ($1, $2) " \
                "ON CONFLICT (user_id) " \
                "DO UPDATE SET avatar = $2"
            _avatar = await self.bot.db.fetchval("SELECT avatar FROM user_settings WHERE user_id = $1", interaction.user.id)
            if _avatar == True:
                await self.bot.db.execute(avatar, interaction.user.id, False)
                await interaction.response.send_message(content = f"Successfully `opted out` for avatar logging **{interaction.user}** <a:AnimeSmile:915132366094209054>", ephemeral = True)
            await self.bot.db.execute(avatar, interaction.user.id, True)
            await interaction.response.send_message(content = f"Successfully `opted in` for avatar logging **{interaction.user}** <a:AnimeSmile:915132366094209054>", ephemeral = True)
        
        if self.values[0] == "username":
            username = "INSERT INTO user_settings (user_id, username) VALUES ($1, $2) " \
                "ON CONFLICT (user_id) " \
                "DO UPDATE SET username = $2"
            _username = await self.bot.db.fetchval("SELECT username FROM user_settings WHERE user_id = $1", interaction.user.id)
            if _username == True:
                await self.bot.db.execute(username, interaction.user.id, False)
                await interaction.response.send_message(content = f"Successfully `opted out` for username logging **{interaction.user}** <a:AnimeSmile:915132366094209054>", ephemeral = True)
            await self.bot.db.execute(avatar, interaction.user.id, True)
            await interaction.response.send_message(content = f"Successfully `opted in` for username logging **{interaction.user}** <a:AnimeSmile:915132366094209054>", ephemeral = True)
        
        if self.values[0] == "discriminator":
            discriminator = "INSERT INTO user_settings (user_id, discriminator) VALUES ($1, $2) " \
                "ON CONFLICT (user_id) " \
                "DO UPDATE SET discriminator = $2"
            _discriminator = await self.bot.db.fetchval("SELECT discriminator FROM user_settings WHERE user_id = $1", interaction.user.id)
            if _discriminator == True:
                await self.bot.db.execute(discriminator, interaction.user.id, False)
                await interaction.response.send_message(content = f"Successfully `opted out` for discriminator logging **{interaction.user}** <a:AnimeSmile:915132366094209054>", ephemeral = True)
            await self.bot.db.execute(avatar, interaction.user.id, True)
            await interaction.response.send_message(content = f"Successfully `opted in` for discriminator logging **{interaction.user}** <a:AnimeSmile:915132366094209054>", ephemeral = True)
