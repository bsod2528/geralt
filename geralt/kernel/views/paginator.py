from __future__ import annotations

from typing import TYPE_CHECKING, List

import discord
from discord import ButtonStyle, NotFound

from ...context import BaseContext
from ...embed import BaseEmbed

if TYPE_CHECKING:
    from ...bot import BaseBot

# Sub - class for paginator using buttons. Button style and label has been
# inspired from RoboDanny [Discord.py Bot] by "Danny aka Rapptz" -> Github
# Profile


class Paginator(discord.ui.View):
    """A simple paginator by subclass `:class: ~ discord.ui.View`.
    Thus creating a pagination by switching to different embeds using the buttons
    created.

    Attributes:
    -----------
    self.bot: geralt.BaseBot()
        Custom commands.Bot subclass
    self.ctx: geralt.BaseContext()
        Custom commands.Context subclass
    self.total: int
        Total number of embeds
    self.embeds: List[BaseEmbed]
        List of embeds to be paginated
    self.current: int
        Current embed index
    """

    def __init__(self, bot: BaseBot, ctx: BaseContext, embeds: List[BaseEmbed]):
        super().__init__(timeout=80)
        self.bot = bot
        self.ctx = ctx
        self.total = len(embeds)
        self.embeds = embeds
        self.current = 0

        if self.total >= 1:
            self.left.disabled = True
            self.max_left.disabled = True
        if ctx.interaction:
            self.delete.disabled = True

    @discord.ui.button(label="<<", style=ButtonStyle.gray)
    async def max_left(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.current = 0
        self.left.disabled = True
        button.disabled = True

        if self.total >= 1:
            self.right.disabled = False
            self.max_right.disabled = False
        else:
            self.right.disabled = True
            self.max_right.disabled = True
        try:
            await interaction.response.edit_message(
                embed=self.embeds[self.current], view=self
            )
        except NotFound:
            return

    @discord.ui.button(label="<", style=ButtonStyle.blurple)
    async def left(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current -= 1

        if self.total >= 1:
            self.max_right.disabled = False
            self.right.disabled = False
        else:
            self.max_right.disabled = True
            self.right.disabled = True

        if self.current <= 0:
            self.current = 0
            self.max_left.disabled = True
            button.disabled = True
        else:
            self.max_left.disabled = False
            button.disabled = False

        try:
            await interaction.response.edit_message(
                embed=self.embeds[self.current], view=self
            )
        except NotFound:
            return

    @discord.ui.button(label=">", style=ButtonStyle.blurple)
    async def right(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current += 1

        if self.current >= self.total - 1:
            self.current = self.total - 1
            button.disabled = True
            self.max_right.disabled = True

        if len(self.embeds) >= 1:
            self.max_left.disabled = False
            self.left.disabled = False
        else:
            self.left.disabled = True
            self.max_left.disabled = True

        try:
            await interaction.response.edit_message(
                embed=self.embeds[self.current], view=self
            )
        except NotFound:
            return

    @discord.ui.button(label=">>", style=ButtonStyle.gray)
    async def max_right(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.current = self.total - 1

        button.disabled = True
        self.right.disabled = True

        if self.total >= 1:
            self.max_left.disabled = False
            self.left.disabled = False
        else:
            self.max_left.disabled = True
            self.left.disabled = True

        try:
            await interaction.response.edit_message(
                embed=self.embeds[self.current], view=self
            )
        except NotFound:
            return

    @discord.ui.button(label="Exit", style=ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()

    async def send(self, ctx: BaseContext):
        self.message = await ctx.reply(
            embed=self.embeds[0], view=self, mention_author=False
        )
        return self.message

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

    async def on_timeout(self) -> None:
        try:
            for view in self.children:
                view.disabled = True
                await self.message.edit(view=self)
        except NotFound:
            return
