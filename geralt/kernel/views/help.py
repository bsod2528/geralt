from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List

import discord
from discord.errors import NotFound
from discord.ext.commands import Cog, Command, Group

from ...context import BaseContext
from ...embed import BaseEmbed

if TYPE_CHECKING:
    from ...bot import BaseBot
    from ..help import BaseHelp


class HelpMenu(discord.ui.Select):
    """Subclass of `:class: discord.ui.Select which` handles
    all the interactions when a user
    invokes the Help Command and changing the cog.

    Attributes:
    -----------
    bot: geralt.bot.BaseBot
        The main bot instance.
    ctx: geralt.context.Context
        Subclass of :class: `commands.Context`.
    help: help.BaseBotHelp
        Subclass of :class: `commands.HelpCommand`.
    mapping: typing.Dict
        Dict with cogs as key and commands as value.

    Parameters:
    ----------
    mapping: typing.Dict
    help: help.BaseBotHelp
    ctx: geralt.context.Context
    """

    def __init__(
            self,
            mapping: Dict[Cog, Command],
            help: BaseHelp,
            cog_list: List[Cog]):
        options = [
            discord.SelectOption(
                label=cog.qualified_name,
                description=cog.description,
                emoji=cog.emote) for cog in cog_list]

        super().__init__(
            options=options,
            min_values=1,
            max_values=1,
            placeholder="Choose a cog")
        self.bot: BaseBot = help.context.bot
        self.ctx: BaseContext = help.context
        self.help: BaseHelp = help
        self.mapping = mapping

    async def callback(self, interaction: discord.Interaction):
        for cog, commands in self.mapping.items():
            emote = getattr(cog, "emote", None)
            if cog is not None:
                if self.values[0] == cog.qualified_name:
                    callback_emb = BaseEmbed(
                        title=f"{cog.qualified_name} Commands",
                        description=f"{cog.description} {emote}" if cog and cog.description else "Description Yet to be Given",
                        colour=self.bot.colour)
                    filtered_commands = await self.help.filter_commands(commands, sort=True)
                    for commands in filtered_commands:
                        callback_emb.add_field(
                            name=f"<:Join:932976724235395072> {commands.qualified_name}",
                            value=f"> ` ─ ` {commands.short_doc} {'<:G:915108274263703553>' if isinstance(commands, Group) else ' '}" or "Yet to be documented",
                            inline=False)
                        callback_emb.set_thumbnail(
                            url=self.ctx.me.display_avatar)
                        callback_emb.set_footer(
                            text=self.help.main_footer(),
                            icon_url=self.ctx.author.display_avatar)
        await interaction.response.edit_message(embed=callback_emb)


class HelpView(discord.ui.View):
    """Subclass of `:class: discord.ui.View which` handles
    all the interactions when a user
    invokes the Help Command.

    Attributes:
    -----------
    help: help.BaseHelp
        Subclass of :class: `commands.HelpCommand`.
    mapping: Dict
        Dict with cogs as key and commands as value.
    ctx: geralt.context.Context
        Subclass of :class: `commands.Context`.
    footer: str
        A sentence for setting footers on embeds.

    Parameters:
    ----------
    help: help.BaseHelp
    mapping
    cog_list: List[`commands.Cog`]
    """

    def __init__(
            self,
            mapping,
            help: BaseHelp,
            cog_list):
        super().__init__(timeout=100)
        self.help: BaseHelp = help
        self.mapping = mapping
        self.ctx = help.context
        self.add_item(HelpMenu(mapping, help, cog_list))

        if self.ctx.interaction:
            self.delete.disabled = True

    def footer(self):
        return f"Run {self.ctx.clean_prefix}help [cog | command] for more info."

    @discord.ui.button(label="Home",
                       style=discord.ButtonStyle.grey,
                       emoji="\U0001f3d8",
                       row=2)
    async def home(self, interaction: discord.Interaction, button: discord.ui.Button):
        help_emb = BaseEmbed(
            title=f"\U00002728 {self.ctx.author}'s Help",
            description=f"────\nHi! I am [**BaseBot**](https://github.com/BSOD2528/BaseBot) and open source Discord Bot made for fun.\n────",
            colour=self.ctx.bot.colour)

        for cog, commands in self.mapping.items():
            filtered_cmds = await self.help.filter_commands(commands, sort=True)
            if filtered_cmds:
                if cog is None:
                    continue
                emote = getattr(cog, "emote", None)
                help_emb.add_field(
                    name=f"{emote} {cog.qualified_name}",
                    value=f"<:Join:932976724235395072> `{self.ctx.clean_prefix}help {cog.qualified_name}`",
                    inline=True)
                help_emb.set_thumbnail(url=self.ctx.me.display_avatar)
                help_emb.set_footer(
                    text=self.footer(),
                    icon_url=self.ctx.author.display_avatar)
        await interaction.response.edit_message(embed=help_emb, view=self)

    @discord.ui.button(label="Updates",
                       style=discord.ButtonStyle.grey,
                       emoji="<a:Info:905750331789561856>",
                       row=2)
    async def updates(self, interaction: discord.Interaction, button: discord.ui.Button):
        updates_emb = BaseEmbed(
            title="Latest Updates",
            description=f"The following points list down the latest updates made as of <t:1673797463:D> (<t:1673797463:R>)",
            colour=self.ctx.bot.colour)
        updates_emb.add_field(
            name="Updates :", value=f">>> <:One:989876071052750868> <t:1673797463:D> ─ <:Emote:1044584258578157588> Added `{self.ctx.clean_prefix}emote delete/rename`.\n"
            f"<:Two:989876145291948122> <t:1673797463:D> ─ General Patch.\n"
            f"<:Three:989876184420610099> <t:1669255064:D> ─ <:Server:1044584714331242496> Added `{self.ctx.clean_prefix}guild auditlog` - </guild auditlog:1003921251238166589>\n"
            f"<:Four:1002832347240083486> <t:1644587100:D> ─ <:SarahPray:920484222421045258> Added `{self.ctx.clean_prefix}urban - </urban:1037360284655964292>")
        updates_emb.set_footer(
            text=self.help.main_footer(),
            icon_url=self.ctx.author.display_avatar.url)
        await interaction.response.edit_message(embed=updates_emb, view=self)

    @discord.ui.button(label="Arg-Usage",
                       style=discord.ButtonStyle.grey,
                       emoji="<a:Verify:905748402871095336>",
                       row=2)
    async def arg_usage(self, interaction: discord.Interaction, button: discord.ui.Button):
        arg_usage_emb = BaseEmbed(
            title=":scroll: Argument Usage", description=f"The following showcase how you are supposed to pass in arguments for invoking commands using `{self.ctx.clean_prefix}`. "
            f"An \"**argument**\" is a value that is passed into the command in order to successfully invoke the command.\n"
            f"\n> <:Join:932976724235395072> `<argument>` : Compulsory Argument\n> <:Join:932976724235395072> `[argument]` : Optional Argument\n"
            f"> <:Join:932976724235395072> `[argument A | argument B]` : Either Argument A or B\n> <:Join:932976724235395072> `[argument ...]` : Multiple values are to be passed\n"
            f"> <:Join:932976724235395072> `[--flags]` : These are arguments passed in via using flags. `--` has to be used before passing in the value.\n\n"
            f"When passing in arguemnts, ensure not to type `<> / []`. Those symbols are used to represent the type of argument they are.", colour=self.help.context.bot.colour)
        arg_usage_emb.set_footer(
            text=self.help.main_footer(),
            icon_url=self.ctx.author.display_avatar.url)
        await interaction.response.edit_message(embed=arg_usage_emb, view=self)

    @discord.ui.button(label="Delete",
                       style=discord.ButtonStyle.red,
                       emoji="<a:Trash:906004182463569961>",
                       row=2)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.ctx.add_nanotick()
            return await interaction.message.delete()
        except NotFound:
            return await interaction.response.send_message(content="You cannot delete messages in ephemeral messages", ephemeral=True)

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
                return await interaction.response.send_message(content=f"{pain}", ephemeral=True)
            except NotFound:
                return
        return True


class GroupAndCommandView(discord.ui.View):
    """Subclass of `:class: discord.ui.View which` handles
    all the interactions when a user
    invokes the Help Command for a Group or a Command.

    Attributes:
    -----------
    help: help.BaseBotHelp
        Subclass of :class: `commands.HelpCommand`.
    mapping: Dict
        Dict with cogs as key and commands as value.
    footer: str
        A sentence for setting footers on embeds.

    Parameters:
    ----------
    help: help.BaseHelp
    mapping
    """

    def __init__(self, help: BaseHelp, mapping):
        super().__init__(timeout=60)
        self.help = help
        self.mapping = mapping

        if self.help.context.interaction:
            self.delete.disabled = True

    def footer(self):
        return f"Run {self.help.context.clean_prefix}help [cog | command] for more info."

    @discord.ui.button(label="Home",
                       style=discord.ButtonStyle.grey,
                       emoji="\U0001f3d8")
    async def home(self, interaction: discord.Interaction, button: discord.ui.Button):
        help_emb = BaseEmbed(
            title=f"\U00002728 {self.help.context.author}'s Help",
            description=f"────\nHi! I am [**BaseBot**](https://github.com/BSOD2528/BaseBot) and open source Discord Bot made for fun.\n────",
            colour=self.help.context.bot.colour)
        cog_list: List[commands.Cog] = []
        for cog, commands in self.mapping.items():
            filtered_cmds = await self.help.filter_commands(commands, sort=True)
            if filtered_cmds:
                if cog is None:
                    continue
                cog_list.append(cog)
                emote = getattr(cog, "emote", None)
                help_emb.add_field(
                    name=f"{emote} {cog.qualified_name}",
                    value=f"<:Join:932976724235395072> `{self.help.context.clean_prefix}help {cog.qualified_name}`",
                    inline=True)
                help_emb.set_thumbnail(url=self.help.context.me.display_avatar)
                help_emb.set_footer(
                    text=self.footer(),
                    icon_url=self.help.context.author.display_avatar)
        button.disabled = True
        try:
            await interaction.response.edit_message(embed=help_emb, view=self)
        except NotFound:
            return

    @discord.ui.button(label="Delete",
                       style=discord.ButtonStyle.red,
                       emoji="<a:Trash:906004182463569961>")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            return await interaction.message.delete()
        except NotFound:
            return

    async def on_timeout(self) -> None:
        try:
            for view in self.children:
                view.disabled = True
            await self.message.edit(view=self)
        except NotFound:
            return

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{self.help.context.clean_prefix}{self.help.context.command}` for the `{self.help.context.command}` command <:SarahPray:920484222421045258>"
        if interaction.user != self.help.context.author:
            try:
                return await interaction.response.send_message(content=f"{pain}", ephemeral=True)
            except NotFound:
                return
        return True
