import discord

from discord.ext import commands
from typing import Union, Optional
from discord.ext.commands import Group
from discord.ext.commands import HelpCommand

from ...kernel.subclasses.embed import BaseEmbed
from ...kernel.views.help import GroupAndCommandView, HelpView
from ...kernel.subclasses.context import GeraltContext


class GeraltHelp(commands.HelpCommand):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.context: GeraltContext

    def footer(self):
        return f"Run {self.context.clean_prefix}help [cog | command] for more info."

    def group_and_command_footer(
            self, group_or_command: Union[commands.Command, commands.Group]):
        return f"Run \"{self.context.clean_prefix}help {group_or_command.cog_name}\" for info on \"{group_or_command.cog_name}\" cog."

    async def send_bot_help(self, mapping) -> Optional[discord.Message]:
        cog_list = []
        help_emb = BaseEmbed(
            title=f"\U00002728 {self.context.author}'s Help",
            description=f"────\nHi! I am [**Geralt**](https://github.com/BSOD2528/Geralt) and open source Discord Bot made for fun.\n────",
            colour=self.context.bot.colour)

        for cog, commands in mapping.items():
            filtered_cmds = await self.filter_commands(commands, sort=True)
            if filtered_cmds:
                if cog is None:
                    continue
                cog_list.append(cog)
                emote = getattr(cog, "emote", None)
                help_emb.add_field(
                    name=f"{emote} {cog.qualified_name}",
                    value=f"<:Join:932976724235395072> `{self.context.clean_prefix}help {cog.qualified_name}`",
                    inline=True)
                help_emb.set_thumbnail(url=self.context.me.display_avatar)
                help_emb.set_footer(
                    text=self.footer(),
                    icon_url=self.context.author.display_avatar)
        main_help_view: discord.ui.View = HelpView(mapping, self, cog_list)
        main_help_view.message = await self.context.reply(embed=help_emb, view=main_help_view, mention_author=False)
        await main_help_view.wait()

    async def send_cog_help(self, cog: commands.Cog) -> Optional[discord.Message]:
        cog.get_commands()
        emote = getattr(cog, "emote", None)
        cog_emb = BaseEmbed(
            title=f"{cog.qualified_name} Commands",
            description=f"{cog.description} {emote}\n" if cog and cog.description else "Description Yet to be Given",
            colour=self.context.bot.colour)

        filtered_commands = await self.filter_commands(cog.get_commands(), sort=True)
        for commands in filtered_commands:
            cog_emb.add_field(
                name=f"<:Join:932976724235395072> {commands.qualified_name}",
                value=f"> ` ─ ` {commands.short_doc} {'<:G:915108274263703553>' if isinstance(commands, Group) else ' '}" or "Yet to be documented",
                inline=False)
            cog_emb.set_thumbnail(url=self.context.me.display_avatar)
            cog_emb.set_footer(text=self.footer(),
                               icon_url=self.context.author.display_avatar)
            if self.context.author.id in self.context.bot.owner_ids:
                cog_list = [
                    cogs for cogs in HelpCommand.get_bot_mapping(self) if cogs is not None and cogs.qualified_name not in [
                        "ErrorHandler", "Jishaku", "Events", "Help"]]
            else:
                cog_list = [
                    cogs for cogs in HelpCommand.get_bot_mapping(self) if cogs is not None and cogs.qualified_name not in [
                        "ErrorHandler", "Developer", "Jishaku", "Events", "Help"]]
        try:
            cog_view: discord.ui.View = HelpView(HelpCommand.get_bot_mapping(self), self, cog_list)
            cog_view.message = await self.context.reply(embed=cog_emb, mention_author=False, view=cog_view)
            await cog_view.wait()
        except BaseException:
            return

    async def send_command_help(self, command: commands.Command) -> Optional[discord.Message]:
        try:
            await command.can_run(self.context)
        except BaseException:
            return
        if command.aliases:
            alias = " | ".join(f"`{alias}`" for alias in sorted(command.aliases))
        else:
            alias = "`Nil`"
        emote = getattr(command._cog, "emote", None)

        command_emb = BaseEmbed(
            title=f"{command} Help {emote}",
            colour=self.context.bot.colour)
        command_emb.set_footer(
            text=self.group_and_command_footer(command),
            icon_url=self.context.author.display_avatar)

        if cooldown := command._buckets._cooldown:
            bucket = command._buckets.type
            {"by" if bucket.name == "user" else "in"}
            command_emb.add_field(
                name="<:GeraltRightArrow:904740634982760459> Cooldown :",
                value=f"> ` ─ ` Can be used `{cooldown.rate}` time{'' if cooldown.rate == 1 else 's'} every `{cooldown.per}` seconds a **`{bucket.name}`**.",
                inline=False)

        if concurrency := command._max_concurrency:
            {'by' if concurrency.per.name == 'user' else 'in'}
            command_emb.add_field(
                name="<:GeraltRightArrow:904740634982760459> Concurrency :",
                value=f"> ` ─ ` Can be used `{concurrency.number}` time{'' if concurrency.number == 1 else 's'} concurrently in a **`{concurrency.per.name}`**.",
                inline=False)

        if self.context.author.is_on_mobile():
            command_emb.description = f"```yaml\n> Syntax : {self.context.clean_prefix}{command.qualified_name} {command.signature}\n```\n" \
                                      f">>> <:ReplyContinued:930634770004725821> ` ─ ` **Aliases : ** [{alias}]\n<:ReplyContinued:930634770004725821> ` ─ ` **Category :** {command.cog_name} \n" \
                                      f"<:Reply:930634822865547294> ` ─ ` **Description : ** {command.help if command.help else '`. . .`'}\n{f'<:Join:932976724235395072> ` ─ ` **Parent Command :** `{command.full_parent_name}`' if command.parent else ' '}"
            command_view_for_mobile: discord.ui.View = GroupAndCommandView(self, HelpCommand.get_bot_mapping(self))
            command_view_for_mobile.message = await self.context.reply(embed=command_emb, mention_author=False, view=command_view_for_mobile)
            await command_view_for_mobile.wait()
        else:
            command_emb.description = f"```ansi\n\x1b[0;1;37;40m > \x1b[0m \x1b[0;1;31mSyntax\x1b[0m \x1b[0;1;37;40m : \x1b[0m \x1b[0;1;37m{self.context.clean_prefix}{command.qualified_name}\x1b[0m \x1b[0;1;34m{command.signature}\x1b[0m\n```\n" \
                                      f">>> <:ReplyContinued:930634770004725821> ` ─ ` **Aliases : ** [{alias}]\n<:ReplyContinued:930634770004725821> ` ─ ` **Category :** {command.cog_name} \n" \
                                      f"<:Reply:930634822865547294> ` ─ ` **Description : ** {command.help if command.help else '`. . .`'}\n{f'<:Join:932976724235395072> ` ─ ` **Parent Command :** `{command.full_parent_name}`' if command.parent else ' '}"
            command_view_for_pc: discord.ui.View = GroupAndCommandView(self, HelpCommand.get_bot_mapping(self))
            command_view_for_pc.message = await self.context.reply(embed=command_emb, mention_author=False, view=command_view_for_pc)
            await command_view_for_pc.wait()

    async def send_group_help(self, group: commands.Group) -> Optional[discord.Message]:
        try:
            await group.can_run(self.context)
        except BaseException:
            return
        group_commands = [
            f"> <:Join:932976724235395072> `{command.name}{' '*(10 - len(command.name))}` \u200b ─ \u200b {command.short_doc}" for command in group.commands]
        if group.aliases:
            alias = " | ".join(f"`{alias}`" for alias in sorted(group.aliases))
        else:
            alias = "`Nil`"
        emote = getattr(group._cog, "emote", None)

        group_emb = BaseEmbed(
            title=f"{group} Help {emote}",
            colour=self.context.bot.colour)
        group_emb.add_field(
            name="Subcommands Present :",
            value=f"\n".join(sorted(group_commands)))
        group_emb.set_footer(
            text=self.group_and_command_footer(group),
            icon_url=self.context.author.display_avatar)

        if cooldown := group._buckets._cooldown:
            bucket = group._buckets._type
            {"by" if bucket.name == "user" else "in"}
            group_emb.add_field(
                name="<:GeraltRightArrow:904740634982760459> Cooldown :",
                value=f"> ` ─ ` Can be used `{cooldown.rate}` time{'' if cooldown.rate == 1 else 's'} every `{cooldown.per}` seconds a **`{bucket.name}`**.",
                inline=False)

        if concurrency := group._max_concurrency:
            {'by' if concurrency.per.name == 'user' else 'in'}
            group_emb.add_field(
                name="<:GeraltRightArrow:904740634982760459> Concurrency :",
                value=f"> ` ─ ` Can be used `{concurrency.number}` time{'' if concurrency.number == 1 else 's'} concurrently in a **`{concurrency.per.name}`**.",
                inline=False)

        if self.context.author.is_on_mobile():
            group_emb.description = f"```yaml\n> Syntax : {self.context.clean_prefix}{group} {group.signature}\n```\n" \
                                    f">>> <:ReplyContinued:930634770004725821>` ─ ` **Aliases : ** [{alias}]\n<:ReplyContinued:930634770004725821>` ─ ` **Category :** {group.cog_name}\n" \
                                    f"<:Reply:930634822865547294>` ─ ` **Description : ** {group.help}"
            group_view_for_mobile: discord.ui.View = GroupAndCommandView(self, HelpCommand.get_bot_mapping(self))
            group_view_for_mobile.message = await self.context.reply(embed=group_emb, mention_author=False, view=group_view_for_mobile)
            await group_view_for_mobile.wait()
        else:
            group_emb.description = f"```ansi\n\x1b[0;1;37;40m > \x1b[0m \x1b[0;1;31mSyntax\x1b[0m \x1b[0;1;37;40m : \x1b[0m \x1b[0;1;37m{self.context.clean_prefix}{group}\x1b[0m \x1b[0;1;34m{group.signature}\x1b[0m\n```\n" \
                                    f">>> <:ReplyContinued:930634770004725821>` ─ ` **Aliases : ** [{alias}]\n<:ReplyContinued:930634770004725821>` ─ ` **Category :** {group.cog_name}\n" \
                                    f" <:Reply:930634822865547294>` ─ ` **Description : ** {group.help}"
            group_view_for_pc: discord.ui.View = GroupAndCommandView(self, HelpCommand.get_bot_mapping(self))
            group_view_for_pc.message = await self.context.reply(embed=group_emb, mention_author=False, view=group_view_for_pc)
            await group_view_for_pc.wait()

    async def send_error_message(self, error: str, /) -> None:
        error_emb = BaseEmbed(
            description=error,
            colour=discord.Colour.from_rgb(231, 77, 60))
        await self.context.reply(embed=error_emb, mention_author=False)
