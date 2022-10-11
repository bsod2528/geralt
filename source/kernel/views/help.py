import discord

from discord.ext import commands
from discord.errors import NotFound
from discord.ext.commands import Group
from typing import TYPE_CHECKING, Union

from ..subclasses.embed import BaseEmbed
from ..subclasses.context import GeraltContext

if TYPE_CHECKING:
    from ..subclasses.bot import Geralt
    from ...cogs.help.help import GeraltHelp

class HelpMenu(discord.ui.Select):
    def __init__(self, mapping, help, cog_list):
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
        self.bot: "Geralt" = help.context.bot
        self.ctx: GeraltContext = help.context
        self.help = help
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
                            text=self.help.footer(),
                            icon_url=self.ctx.author.display_avatar)
        try:
            await interaction.response.edit_message(embed=callback_emb)
        except NotFound:
            return


class HelpView(discord.ui.View):
    def __init__(self, mapping, help, cog_list):
        super().__init__(timeout=100)
        self.help: "GeraltHelp" = help
        self.mapping = mapping
        self.ctx: GeraltContext = help.context
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
            description=f"────\nHi! I am [**Geralt**](https://github.com/BSOD2528/Geralt) and open source Discord Bot made for fun.\n────",
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
        try:
            await interaction.response.edit_message(embed=help_emb, view=self)
        except NotFound:
            return

    @discord.ui.button(label="Updates",
                       style=discord.ButtonStyle.grey,
                       emoji="\U0001f4dc",
                       row=2)
    async def updates(self, interaction: discord.Interaction, button: discord.ui.Button):
        updates_emb = BaseEmbed(
            title="Latest Updates",
            description=f"The following points list down the latest updates made as of <t:1664774386:D> (<t:1664774386:R>)",
            colour=self.ctx.bot.colour)
        updates_emb.add_field(
            name="Updates :",
            value=f">>> <:One:989876071052750868> <t:1664774386:D> ─ <a:Nope:988845795920990279> Added `{self.ctx.clean_prefix}highlight` - </highlight add:1025824025563377746> to begin!\n"
            f"<:Two:989876145291948122> <t:1664774386:D> ─ <:WinCogs:898591890209910854> Added `Discord Cog` with commands switched from `Utility Cog` to here.\n"
            f"<:Three:989876184420610099> <t:1664774386:D> ─ <:SlashCommands:1026146843295498340> Slashified the help command. \n"
            f"<:Four:1002832347240083486> <t:1664774386:D> ─ <:TicketHelp:987182220626235482> Added `{self.ctx.clean_prefix}avatarhistory` & `{self.ctx.clean_prefix}emote`. Available as slash to - </avatarhistory:1017741037902516278> </emote:1019843698332282900>\n"
            f"<:Five:1002832404051935282> <t:1659450876:D> ─ <:SarahPray:920484222421045258> Added more slash commands. Type out `/` to see them all.\n")
        updates_emb.set_footer(
            text=self.help.footer(),
            icon_url=self.ctx.me.display_avatar)
        try:
            await interaction.response.edit_message(embed=updates_emb, view=self)
        except NotFound:
            return

    @discord.ui.button(label="Arg-Usage",
                       style=discord.ButtonStyle.grey,
                       emoji="<a:Verify:905748402871095336>",
                       row=2)
    async def arg_usage(self, interaction: discord.Interaction, button: discord.ui.Button):
        arg_usage_emb = BaseEmbed(
            title=":scroll: Argument Usage",
            description=f"The following showcase how you are supposed to pass in arguments for invoking commands using `{self.ctx.clean_prefix}`. "
            f"An \"**argument**\" is a value that is passed into the command in order to successfully invoke the command.\n"
            f"\n> <:Join:932976724235395072> `<argument>` : Compulsory Argument\n> <:Join:932976724235395072> `[argument]` : Optional Argument\n"
            f"> <:Join:932976724235395072> `[argument A | argument B]` : Either Argument A or B\n> <:Join:932976724235395072> `[argument ...]` : Multiple values are to be passed\n"
            f"> <:Join:932976724235395072> `[--flags]` : These are arguments passed in via using flags. `--` has to be used before passing in the value.\n\n"
            f"When passing in arguemnts, ensure not to type `<> / []`. Those symbols are used to represent the type of argument they are.",
            colour=self.help.context.bot.colour)
        arg_usage_emb.set_footer(
            text=self.help.footer(),
            icon_url=self.help.context.me.display_avatar)
        try:
            await interaction.response.edit_message(embed=arg_usage_emb, view=self)
        except NotFound:
            return

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


class SearchCommand(discord.ui.Modal, title="Search Command"):
    def __init__(self, help, command: Union[commands.command, Group]):
        super().__init__()
        self.help = help
        self.command = command

    command = discord.ui.TextInput(
        label="Command Name",
        required=True,
        placeholder="Search a command.")

    async def on_submit(self, interaction: discord.Interaction) -> None:
        command_list = await self.help.context.bot.commands()

class GroupAndCommandView(discord.ui.View):
    def __init__(self, help, mapping):
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
            description=f"────\nHi! I am [**Geralt**](https://github.com/BSOD2528/Geralt) and open source Discord Bot made for fun.\n────",
            colour=self.help.context.bot.colour)
        cog_list = []
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
        try:
            await interaction.response.edit_message(embed=help_emb, view=HelpView(self.mapping, self.help, cog_list))
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
