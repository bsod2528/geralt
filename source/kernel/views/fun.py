import random
import discord

from discord.ext import commands
from discord.errors import NotFound
from typing import Optional, TYPE_CHECKING

from ..subclasses.embed import BaseEmbed
from ..subclasses.context import GeraltContext

if TYPE_CHECKING:
    from ..subclasses.bot import Geralt

# Nitro Command View


class Nitro(discord.ui.View):
    def __init__(self, ctx: GeraltContext):
        super().__init__()
        self.ctx: GeraltContext = ctx

    @discord.ui.button(label="Avail Nitro",
                       style=discord.ButtonStyle.green,
                       emoji="<a:WumpusHypesquad:905661121501990923>")
    async def nitro(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled = True
        button.label = "Claimed"
        await interaction.message.edit(view=self)
        try:
            await interaction.user.send(content=f"discord.gift/R1cKr0OlL3d")
            await interaction.response.send_message(content="https://imgur.com/NQinKJB", ephemeral=True)
        except Exception as exception:
            try:
                await interaction.response.send_message(content=f"```py\n{exception}\n```", ephemeral=True)
            except NotFound:
                return

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{self.ctx.clean_prefix}{self.ctx.command}` for the `{self.ctx.command}` command <:SarahPray:920484222421045258>"
        if interaction.user != self.ctx.author:
            try:
                return await interaction.response.send_message(content=f"{pain}", ephemeral=True)
            except NotFound:
                return
        return True

# Classes for Pop Game


class PopSize(
        commands.FlagConverter,
        prefix="--",
        delimiter=" ",
        case_insensitive=False):
    size: Optional[int]


class PopButton(discord.ui.Button):
    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            self.disabled = True
            self.style = discord.ButtonStyle.grey
            await self.view.message.edit(view=self.view)
        except NotFound:
            return


class Pop(discord.ui.View):
    def __init__(self, ctx: GeraltContext, *, size: Optional[PopSize]):
        super().__init__(timeout=90)
        self.ctx: GeraltContext = ctx
        self.size = size
        self.message: Optional[discord.Message] = None

    async def send(self):
        try:
            for button in range(self.size):
                if self.size > 25:
                    raise commands.BadArgument(
                        "size passed in should be less than 25.")
                if not self.size:
                    self.add_item(
                        PopButton(
                            label="Pop",
                            style=discord.ButtonStyle.grey,
                            emoji=random.choice(emoji_list)))
                else:
                    self.add_item(
                        PopButton(
                            label="Pop",
                            style=discord.ButtonStyle.grey,
                            emoji=random.choice(emoji_list)))
            self.message = await self.ctx.send("\u200b", view=self)
        except TypeError:
            return

    async def on_timeout(self) -> None:
        for view in self.children:
            view.disabled = True
            view.style = discord.ButtonStyle.grey
            await self.message.edit(view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{self.ctx.clean_prefix}{self.ctx.command}` for the `{self.ctx.command}` command <:SarahPray:920484222421045258>"
        if interaction.user != self.ctx.author:
            try:
                return await interaction.response.send_message(content=f"{pain}", ephemeral=True)
            except NotFound:
                return
        return True

# Simple Click Game - Idea by InterStella0 [ Github ID ]


class ClickSize(
        commands.FlagConverter,
        prefix="--",
        delimiter=" ",
        case_insensitive=True):
    size: Optional[int]


emoji_list = [
    "<a:Click:973748305416835102>",
    "<:Bonked:934033408106057738>",
    "<a:RooSitComfortPatAnotherRoo:916125535015419954>",
    "<a:IPat:933295620834336819>",
    "<:DuckSip:917006564265705482>",
    "<a:SpongebobVibe:913798501123645480>",
    "<a:ZizzyHappy:915131835443474492>",
    "<a:ReiPet:965800035054931998>"]


class ClickButton(discord.ui.Button):
    def __init__(self, bot: "Geralt", ctx: GeraltContext):
        super().__init__(
            label="Click",
            style=discord.ButtonStyle.grey,
            emoji=random.choice(emoji_list))
        self.bot: "Geralt" = bot
        self.ctx: GeraltContext = ctx

    async def callback(self, interaction: discord.Interaction):
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{self.ctx.clean_prefix}{self.ctx.command}` for the `{self.ctx.command}` command <:SarahPray:920484222421045258>"
        if interaction.user == self.ctx.author:
            try:
                try:
                    await interaction.response.defer()
                    guild_score_query = "INSERT INTO click_guild (guild_id, player_id, clicks, player_name)" \
                        "VALUES ($1, $2, 1, $3)" \
                        "ON CONFLICT (guild_id, player_id)" \
                        "DO UPDATE SET clicks = click_guild.clicks + 1, player_name = $3"
                    await self.bot.db.execute(guild_score_query, interaction.guild_id, interaction.user.id, str(self.ctx.author))
                    global_score_query = "INSERT INTO click_global (player_id, clicks, player_name, player_pfp)" \
                        "VALUES ($1, 1, $2, $3)" \
                        "ON CONFLICT (player_id)" \
                        "DO UPDATE SET clicks = click_global.clicks + 1, player_name = $2, player_pfp = $3"
                    await self.bot.db.execute(global_score_query, interaction.user.id, str(self.ctx.author), str(self.ctx.author.display_avatar))
                except NotFound:
                    return
            except Exception as exception:
                try:
                    await interaction.followup.send(content=f"```py\n{exception}\n```", ephemeral=True)
                except NotFound:
                    return
        else:
            try:
                await interaction.response.send_message(content=f"{pain}", ephemeral=True)
            except NotFound:
                return


class ClickGame(discord.ui.View):
    def __init__(
            self,
            bot: "Geralt",
            ctx: GeraltContext,
            *,
            size: Optional[int]):
        super().__init__(timeout=60)
        self.bot: "Geralt" = bot
        self.ctx: GeraltContext = ctx
        self.size = size

        for button in range(self.size):
            if self.size > 10:
                raise commands.BadArgument("Size should be less than \"10\"")
            if not self.size:
                self.add_item(ClickButton(self.bot, self.ctx))
            else:
                self.add_item(ClickButton(self.bot, self.ctx))

    @discord.ui.button(label="Scores",
                       style=discord.ButtonStyle.grey,
                       emoji="\U00002728",
                       row=2)
    async def on_click_guild_leaderboard(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            guild_score_query = await self.bot.db.fetchval("SELECT (clicks) FROM click_guild WHERE guild_id = $1 AND player_id = $2", interaction.guild_id, self.ctx.author.id)
            await interaction.response.defer()
            if not guild_score_query:
                await interaction.followup.send(content=f"{self.ctx.author.mention} has yet to click on the button in **{interaction.guild.name}** <:TokoOkay:898611996163985410>", ephemeral=True)
            else:
                await interaction.followup.send(content=f"{self.ctx.author.mention} has clicked a total of `{guild_score_query}` times in **{interaction.guild.name}** <:TokoOkay:898611996163985410>", ephemeral=True)
        except Exception as exception:
            try:
                await interaction.followup.send(content=f"```py\n{exception}\n```", ephemeral=True)
            except NotFound:
                return

    @discord.ui.button(label="Help",
                       style=discord.ButtonStyle.green,
                       emoji="<:DuckThumbsUp:917007413259956254>",
                       row=2)
    async def on_click_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        help_content = f"{interaction.user.mention}\n\n────\n> │ ` ─ ` Click on the \"Click\" button to attain points. You have a 60 second time limit. Try to score much as possible.\n> │ ` ─ ` Go up the leaderboard by playing en number of times. Enjoy!\n────\nhttps://imgur.com/a/S0LyjuB"
        try:
            await interaction.followup.send(content=help_content, ephemeral=True)
        except NotFound:
            return

    async def send(self, ctx):
        self.message = await ctx.reply(content="Click as fast as you can and earn points <a:CrazyRolex:966181282914660402>", view=self)
        return self.message

    async def on_timeout(self) -> None:
        for view in self.children:
            view.disabled = True
        return await self.message.edit(content=f"**{self.ctx.author}** - you've been timed out due to inactivity. To start clicking again, rerun `{self.ctx.clean_prefix}{self.ctx.command}` and be the number one on the leaderboard <a:Comfort:918844984621428787>", view=self)


class ClickLeaderboard(discord.ui.View):
    def __init__(self, bot: "Geralt", ctx: GeraltContext):
        super().__init__(timeout=60)
        self.bot: "Geralt" = bot
        self.ctx: GeraltContext = ctx

    @discord.ui.button(label="Global Leaderboard",
                       style=discord.ButtonStyle.grey,
                       emoji="<a:RooSitComfortPatAnotherRoo:916125535015419954>")
    async def click_global_leaderboard(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer()
            global_leaderboard_query = await self.bot.db.fetch("SELECT player_name, clicks, player_pfp FROM click_global ORDER BY clicks DESC LIMIT 10")
            serial_no = 1
            leaderboard = []
            for data in global_leaderboard_query:
                leaderboard.append(
                    f"> **{serial_no})** [{data['player_name']}]({data['player_pfp']}) \u200b : `{data['clicks']}`\n")
                serial_no += 1

            while leaderboard:
                global_leaderboard_emb = BaseEmbed(
                    description=f"The following showcases the top 10 scores for `{self.ctx.clean_prefix}click`",
                    colour=self.bot.colour)
                global_leaderboard_emb.add_field(
                    name="Top 10 Global Scores",
                    value=f"".join(leaderboard[:10]))
                global_leaderboard_emb.set_thumbnail(
                    url="https://discords.com/_next/image?url=https%3A%2F%2Fcdn.discordapp.com%2Femojis%2F929249429486178334.gif%3Fv%3D1&w=64&q=75")
                global_leaderboard_emb.set_author(name="Global Click Scores")
                global_leaderboard_emb.set_footer(
                    text=f"Run {self.ctx.clean_prefix}click for more sub ─ commands.")
                leaderboard = leaderboard[10:]
            try:
                await interaction.followup.send(embed=global_leaderboard_emb, ephemeral=True)
            except NotFound:
                return
        except Exception as exception:
            try:
                await interaction.response.send_message(content=f"```py\n{exception}\n```", ephemeral=True)
            except NotFound:
                return

    async def send(self):
        guild_score_query = await self.bot.db.fetch("SELECT player_id, clicks FROM click_guild WHERE guild_id = $1 ORDER BY clicks DESC LIMIT 10", self.ctx.guild.id)
        serial_no = 1
        leaderboard = []
        for data in guild_score_query:
            leaderboard.append(
                f"> **{serial_no}).** <@{data['player_id']}> : `{data['clicks']}`\n")
            serial_no += 1

        if not guild_score_query:
            return await self.ctx.reply(f"No one from **{self.ctx.guild}** has played `{self.ctx.clean_prefix}click` game <a:Noo:915422306896072744>. Feel honoured and be the first one !")
        else:
            while leaderboard:
                leaderboard_emb = BaseEmbed(
                    title=f"Click Scores for {self.ctx.guild} :",
                    description=f"The following showcases the top 10 scores for `{self.ctx.clean_prefix}click`",
                    colour=self.bot.colour)
                leaderboard_emb.add_field(
                    name="Top 10 Scores",
                    value="".join(leaderboard[:10]))
                leaderboard_emb.set_thumbnail(url=self.ctx.guild.icon.url)
                leaderboard_emb.set_footer(
                    text=f"Run {self.ctx.clean_prefix}help click for more sub ─ commands.")
                leaderboard = leaderboard[10:]
        self.message = await self.ctx.reply(embed=leaderboard_emb, view=self, mention_author=False)
        return self.message

    async def on_timeout(self) -> None:
        for view in self.children:
            view.disabled = True
            return await self.message.edit(view=self)
