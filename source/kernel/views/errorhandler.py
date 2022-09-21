import discord
import traceback

from typing import TYPE_CHECKING
from discord.errors import NotFound

from ..subclasses.embed import BaseEmbed
from ..subclasses.context import GeraltContext

if TYPE_CHECKING:
    from ..subclasses.bot import Geralt

# Error - Handler View


class Traceback(discord.ui.View):
    def __init__(self, bot: "Geralt", ctx: GeraltContext, error):
        super().__init__(timeout=60)
        self.bot: "Geralt" = bot
        self.ctx: GeraltContext = ctx
        self.error = error

        if ctx.interaction:
            self.remove_item(self.delete)

    @discord.ui.button(label="Traceback",
                       style=discord.ButtonStyle.grey,
                       emoji="<:WinTerminal:898609124982554635>")
    async def traceback(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled = True
        error = getattr(self.error, "original", self.error)
        error_emb = BaseEmbed(
            title=f"<:GeraltRightArrow:904740634982760459> Command Errored : {self.ctx.command}",
            description=f"```yaml\n Quick Tip : Read the last 2 - 3 lines for proper info.\n```\n```py\n {''.join(traceback.format_exception(type(error), error, error.__traceback__))}\n```\n",
            colour=0x2F3136)
        await interaction.message.edit(view=self)
        try:
            await interaction.response.send_message(embed=error_emb, ephemeral=True)
        except NotFound:
            return

    @discord.ui.button(label="Command Help",
                       style=discord.ButtonStyle.grey,
                       emoji="<a:Trash:906004182463569961>")
    async def cmd_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled = True
        if self.ctx.command.aliases:
            alias = " | ".join(
                f"`{alias}`" for alias in self.ctx.command.aliases)
        else:
            alias = "`Nil`"
        if interaction.user.is_on_mobile():
            command_help = BaseEmbed(
                title=f"<:GeraltRightArrow:904740634982760459> Command Help : {self.ctx.command}",
                description=f"```yaml\n> Syntax : {self.ctx.clean_prefix}{self.ctx.command.qualified_name} {self.ctx.command.signature}\n```\n"
                f">>> <:ReplyContinued:930634770004725821> ` ─ ` **Aliases : ** [{alias}]\n<:ReplyContinued:930634770004725821> ` ─ ` **Category :** {self.ctx.command.cog_name} \n"
                f"<:Reply:930634822865547294> ` ─ ` **Description : ** {self.ctx.command.help if self.ctx.command.help else '`. . .`'}\n{f'<:Join:932976724235395072> ` ─ ` **Parent Command :** `{self.ctx.command.full_parent_name}`' if self.ctx.command.parent else ' '}",
                colour=0x2F3136)
        else:
            command_help = BaseEmbed(
                title=f"<:GeraltRightArrow:904740634982760459> Command Help : {self.ctx.command}",
                description=f"```ansi\n\x1b[0;1;37;40m > \x1b[0m \x1b[0;1;31mSyntax\x1b[0m \x1b[0;1;37;40m : \x1b[0m \x1b[0;1;37m{self.ctx.clean_prefix}{self.ctx.command.qualified_name}\x1b[0m \x1b[0;1;34m{self.ctx.command.signature}\x1b[0m\n```\n"
                f">>> <:ReplyContinued:930634770004725821> ` ─ ` **Aliases : ** [{alias}]\n<:ReplyContinued:930634770004725821> ` ─ ` **Category :** {self.ctx.command.cog_name} \n"
                f"<:Reply:930634822865547294> ` ─ ` **Description : ** {self.ctx.command.help if self.ctx.command.help else '`. . .`'}\n{f'<:Join:932976724235395072> ` ─ ` **Parent Command :** `{self.ctx.command.full_parent_name}`' if self.ctx.command.parent else ' '}",
                colour=0x2F3136)
        command_help.set_footer(
            text=f"Invoked by {interaction.user}",
            icon_url=interaction.user.display_avatar.url)
        await interaction.message.edit(view=self)
        try:
            try:
                await interaction.response.send_message(embed=command_help, ephemeral=True)
            except NotFound:
                return
        except Exception as exception:
            try:
                await interaction.response.send_message(content=exception, ephemeral=True)
            except NotFound:
                return


    @discord.ui.button(label="Delete",
                       style=discord.ButtonStyle.red,
                       emoji="<a:Trash:906004182463569961>")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()

    async def send(self):
        common_error = BaseEmbed(
            title=f"<:GeraltRightArrow:904740634982760459> Command Errored : {self.ctx.command}",
            description=f"```py\n{self.error}\n```",
            colour=0x2F3136)
        common_error.timestamp = discord.utils.utcnow()
        common_error.set_footer(
            text=f"Errored by {self.ctx.author}",
            icon_url=self.ctx.author.display_avatar.url)
        self.message = await self.ctx.reply(embed=common_error, view=self, mention_author=False)
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
                await interaction.response.send_message(content=f"{pain}", ephemeral=True)
            except NotFound:
                return
        return True

# Error - Handler View for commands.BadArgumemt


class CommandSyntax(discord.ui.View):
    def __init__(self, bot: "Geralt", ctx: GeraltContext, error):
        super().__init__(timeout=60)
        self.bot: "Geralt" = bot
        self.ctx: GeraltContext = ctx
        self.error = error

        if ctx.interaction:
            self.remove_item(self.delete)

    @discord.ui.button(label="Command Help",
                       style=discord.ButtonStyle.grey,
                       emoji="<:WumpusNitro:905674712590454834>")
    async def cmd_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled = True
        button.style = discord.ButtonStyle.green
        if self.ctx.command.aliases:
            alias = " | ".join(
                f"`{alias}`" for alias in self.ctx.command.aliases)
        else:
            alias = "`Nil`"
        if interaction.user.is_on_mobile():
            command_help = BaseEmbed(
                title=f"<:GeraltRightArrow:904740634982760459> Command Help : {self.ctx.command}",
                description=f"```yaml\n> Syntax : {self.ctx.clean_prefix}{self.ctx.command.qualified_name} {self.ctx.command.signature}\n```\n"
                f">>> <:ReplyContinued:930634770004725821> ` ─ ` **Aliases : ** [{alias}]\n<:ReplyContinued:930634770004725821> ` ─ ` **Category :** {self.ctx.command.cog_name} \n"
                f"<:Reply:930634822865547294> ` ─ ` **Description : ** {self.ctx.command.help if self.ctx.command.help else '`. . .`'}\n{f'<:Join:932976724235395072> ` ─ ` **Parent Command :** `{self.ctx.command.full_parent_name}`' if self.ctx.command.parent else ' '}",
                colour=0x2F3136)
        else:
            command_help = BaseEmbed(
                title=f"<:GeraltRightArrow:904740634982760459> Command Help : {self.ctx.command}",
                description=f"```ansi\n\x1b[0;1;37;40m > \x1b[0m \x1b[0;1;31mSyntax\x1b[0m \x1b[0;1;37;40m : \x1b[0m \x1b[0;1;37m{self.ctx.clean_prefix}{self.ctx.command.qualified_name}\x1b[0m \x1b[0;1;34m{self.ctx.command.signature}\x1b[0m\n```\n"
                f">>> <:ReplyContinued:930634770004725821> ` ─ ` **Aliases : ** [{alias}]\n<:ReplyContinued:930634770004725821> ` ─ ` **Category :** {self.ctx.command.cog_name} \n"
                f"<:Reply:930634822865547294> ` ─ ` **Description : ** {self.ctx.command.help if self.ctx.command.help else '`. . .`'}\n{f'<:Join:932976724235395072> ` ─ ` **Parent Command :** `{self.ctx.command.full_parent_name}`' if self.ctx.command.parent else ' '}",
                colour=0x2F3136)
        command_help.set_footer(
            text=f"Invoked by {interaction.user}",
            icon_url=interaction.user.display_avatar.url)
        await interaction.message.edit(view=self)
        try:
            try:
                await interaction.response.send_message(embed=command_help, ephemeral=True)
            except NotFound:
                return
        except Exception as exception:
            try:
                await interaction.response.send_message(content=exception, ephemeral=True)
            except NotFound:
                return

    @discord.ui.button(label="Traceback",
                       style=discord.ButtonStyle.grey,
                       emoji="<:WinTerminal:898609124982554635>")
    async def traceback(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled = True
        button.style = discord.ButtonStyle.green
        error = getattr(self.error, "original", self.error)
        error_emb = BaseEmbed(
            title=f"<:GeraltRightArrow:904740634982760459> Command Errored : {self.ctx.command}",
            description=f"```yaml\n Quick Tip : Read the last 2 - 3 lines for proper info.\n```\n```py\n {''.join(traceback.format_exception(type(error), error, error.__traceback__))}\n```\n",
            colour=0x2F3136)
        await interaction.message.edit(view=self)
        try:
            try:
                await interaction.response.send_message(embed=error_emb, ephemeral=True)
            except NotFound:
                return
        except Exception as exception:
            try:
                await interaction.response.send_message(content=exception, ephemeral=True)
            except NotFound:
                return

    @discord.ui.button(label="Delete",
                       style=discord.ButtonStyle.red,
                       emoji="<a:Trash:906004182463569961>")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.message.delete()
        except BaseException:
            return

    async def send(self):
        command_name = f"{self.ctx.clean_prefix}{self.ctx.command} {self.ctx.command.signature}"
        syntax_emb = BaseEmbed(
            title=f"<:GeraltRightArrow:904740634982760459> Command Errored : {self.ctx.clean_prefix}{self.ctx.command}",
            description=f"\n```py\nerror: {self.error}\n|\n| Syntax:\n|\n| => {command_name}\n|    {' ' * (len([item[::-1] for item in command_name[::-1].split(self.error.param.name[::-1], 1)][::-1][0]) - 1)}{'^' * (len(self.error.param.name) + 2)}\n| Click on `Command Help` button for more info.```",
            colour=0x2F3136)
        syntax_emb.set_footer(
            text=f"Run {self.ctx.clean_prefix}help {self.ctx.command}for more help",
            icon_url=self.ctx.author.display_avatar.url)
        self.message = await self.ctx.reply(embed=syntax_emb, view=self, mention_author=False)
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
                return await interaction.response.send_message(content=f"{pain}", ephemeral=True)
            except NotFound:
                return
        return True
