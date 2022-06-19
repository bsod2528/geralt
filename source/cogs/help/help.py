import discord

from discord.ext import commands
from discord.ext.commands import HelpCommand

from ...kernel.views.help import HelpView
from ...kernel.subclasses.bot import Geralt
from ...kernel.subclasses.embed import BaseEmbed
from ...kernel.subclasses.context import GeraltContext
        
class GeraltHelp(commands.HelpCommand):
    def footer(self):
        return f"Run {self.context.clean_prefix}help [category | command] for more info."
    
    def command_footer(self):
        return f"Run {self.context.clean_prefix}help [command] for info on a command."

    async def send_bot_help(self, mapping):
        self.context : GeraltContext
        cog_list = []
        help_emb = BaseEmbed(
            title = f"\U00002728 {self.context.author}'s Help",
            description = f"────\nHi! I am [**Geralt**](https://github.com/BSOD2528/Geralt) and open source Discord Bot made for fun.\n────",
            colour = self.context.bot.colour)
        
        for cog, commands in mapping.items():
            filtered_cmds = await self.filter_commands(commands, sort = True)
            if filtered_cmds:
                if cog is None:
                    continue
                cog_list.append(cog)
                emote = getattr(cog, "emote", None)
                help_emb.add_field(
                    name = f"{emote} {cog.qualified_name}", 
                    value = f"<:Join:932976724235395072> `{self.context.clean_prefix}help {cog.qualified_name}`",
                    inline = True)
                help_emb.set_thumbnail(url = self.context.me.display_avatar)
                help_emb.set_footer(text = self.footer(), icon_url = self.context.author.display_avatar)
        await self.context.reply(embed = help_emb, view = HelpView(mapping, self, cog_list), mention_author = False)

    async def send_cog_help(self, cog : commands.Cog):
        self.context : GeraltContext
        emote = getattr(cog, "emote", None)
        cog_emb = BaseEmbed(
            title = f"{cog.qualified_name} Commands",
            description = f"{emote} {cog.description}" if cog and cog.description else "...",
            colour = self.context.bot.colour)
        
        filtered_commands = await self.filter_commands(cog.get_commands(), sort = True)
        for commands in filtered_commands:
            cog_emb.add_field(
                name = f"<:Join:932976724235395072> {commands.qualified_name}",
                value = f"> ` ─ ` {commands.short_doc}" or "Yet to be documented",
                inline = False)
            cog_emb.set_thumbnail(url = self.context.me.display_avatar)
            cog_emb.set_footer(text = self.footer(), icon_url = self.context.author.display_avatar)
            if self.context.author.id in self.context.bot.owner_ids:
                cog_list = [cogs for cogs in HelpCommand.get_bot_mapping(self) if cogs is not None and cogs.qualified_name not in ["ErrorHandler", "Jishaku", "Events", "Help"]]
            else:
                cog_list = [cogs for cogs in HelpCommand.get_bot_mapping(self) if cogs is not None and cogs.qualified_name not in ["ErrorHandler", "Developer", "Jishaku", "Events", "Help"]]
        
        try:
            await self.context.reply(embed = cog_emb, mention_author = False, view = HelpView(HelpCommand.get_bot_mapping(self), self, cog_list = cog_list))
        except:
            return

    async def send_command_help(self, command : commands.Command):
        try:
            await command.can_run(self.context)
        except:
            return
        if command.aliases:
            alias = " | ".join(f"`{alias}`" for alias in command.aliases)
        else:
            alias = "`Nil`"
        self.context : GeraltContext

        command_emb = BaseEmbed(
            title = f"{command} Help",
            colour = self.context.bot.colour)
        command_emb.set_footer(text = self.command_footer(), icon_url = self.context.author.display_avatar)

        if self.context.author.is_on_mobile():
            command_emb.description = f"```prolog\n> Syntax : {self.context.clean_prefix}{command.qualified_name} {command.signature}\n```\n" \
                                      f">>> ` ─ ` **Aliases : ** [{alias}]\n" \
                                      f" ` ─ ` **Description : ** {command.help if command.help else '`. . .`'}"
            await self.context.reply(embed = command_emb, mention_author = False)
        else:
            command_emb.description = f"```ansi\n[0;1;37;40m > [0m [0;1;31mSyntax[0m [0;1;37;40m : [0m [0;1;37m{self.context.clean_prefix}{command.qualified_name}[0m [0;1;34m{command.signature}[0m\n```\n" \
                                      f">>> ` ─ ` **Aliases : ** [{alias}]\n" \
                                      f" ` ─ ` **Description : ** {command.help if command.help else '`. . .`'}"
            await self.context.reply(embed = command_emb, mention_author = False)
    
    async def send_group_help(self, group : commands.Group):
        try:
            await group.can_run(self.context)
        except:
            return
        group_commands = [f"> <:Join:932976724235395072> `{command.name}` \u200b ─ \u200b {command.short_doc}" for command in group.commands]
        if group.aliases:
            alias = " | ".join(f"`{alias}`" for alias in group.aliases)
        else:
            alias = "`Nil`"
        self.context : GeraltContext

        group_emb = BaseEmbed(
            title = f"{group} Help",
            colour = self.context.bot.colour)
        group_emb.add_field(
            name = "Subcommands Present :",
            value = f"\n".join(group_commands))
        group_emb.set_footer(text = self.footer(), icon_url = self.context.author.display_avatar)

        if self.context.author.is_on_mobile():
            group_emb.description = f"```prolog\n> Syntax : {self.context.clean_prefix}{group} {group.signature}\n```\n" \
                                    f">>> <:ReplyContinued:930634770004725821>` ─ ` **Aliases : ** [{alias}]\n" \
                                    f"<:Reply:930634822865547294>` ─ ` **Description : ** {group.short_doc}"
            await self.context.reply(embed = group_emb, mention_author = False)
        else:
            group_emb.description = f"```ansi\n[0;1;37;40m > [0m [0;1;31mSyntax[0m [0;1;37;40m : [0m [0;1;37m{self.context.clean_prefix}{group}[0m [0;1;34m{group.signature}[0m\n```\n" \
                                    f">>> <:ReplyContinued:930634770004725821>` ─ ` **Aliases : ** [{alias}]\n" \
                                    f" <:Reply:930634822865547294>` ─ ` **Description : ** {group.short_doc}"
            await self.context.reply(embed = group_emb, mention_author = False)
    
    async def send_error_message(self, error: str, /) -> None:
        error_emb = BaseEmbed(
            description = error,
            colour = discord.Colour.from_rgb(231,77,60))
        error_emb.set_author(name = f"Errored by {self.context.author}")
        await self.context.reply(embed = error_emb, mention_author = False)

class Help(commands.Cog):
    """Help Command"""
    def __init__(self, bot : Geralt):
        self.bot : Geralt = bot
        self._original_help_command = bot.help_command
        help_command = GeraltHelp()
        help_command.cog = self
        bot.help_command = help_command

    @property
    def emote(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name = "Help", id = 907110027951742996, animated = True)
    
    async def cog_unload(self):
        self.bot.help_command = self._original_help_command