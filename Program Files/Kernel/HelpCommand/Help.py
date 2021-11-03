import discord
import contextlib
import datetime
from discord.ext import commands
import Kernel.HelpCommand.View.HelpView as HelpView

class CustomHelp(commands.HelpCommand):
    def __init__(self):
        super().__init__(
            command_attrs = {
                'help'  :   'The help command for this bot'
            }
        )
        self.emojis = {
            'Fun'           :       '<:PandaNice:904765669680226315>',
            'Mod'           :       '<:ModBadge:904765450066473031>',
            'AV'            :       '<:WinTerminal:898609124982554635>',
            'Utility'       :       '<:WinGIT:898591166864441345>',
            'Essential'     :       '<:WinCheck:898572324490604605>',
            'Puns'          :       '<:uwu:902119529461727252>',
            'Quotes'        :       '<:AkkoDab:898610956895154288>',
            'Error Handler' :       '<:WinCogs:898591890209910854>',
            'Jishaku'       :       '<:WinCMD:898572428379299880>'
        }
        self.color = 0x2F3136
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)
        self.footer = 'Run .ghelp <command> for more info on each command'

    async def send_bot_help(self, mapping):
        DropDown = HelpView.HelpMenu(self, mapping)
        DropDown.main.set_thumbnail(
            url = self.context.me.display_avatar.url)
        DropDown.main.set_footer(
            text = self.footer)
        DropDown.message = await self.context.reply(embed = DropDown.main, view = DropDown, mention_author = False)
        return

    async def send_cog_help(self, cog):
        cog_help = discord.Embed(
            color = self.color,
            title = f'{self.emojis.get(cog.qualified_name) if self.emojis.get(cog.qualified_name) else None} {cog.qualified_name}',
            description = f'{cog.description}\n\n',
            timestamp = self.context.message.created_at
        )
        for command in cog.walk_commands():
            cog_help.description += f'<:GeraltRightArrow:904740634982760459> `{command.qualified_name}` - {command.brief}\n'
        cog_help.set_footer(
            text = self.footer)
        await self.context.reply(embed = cog_help, mention_author = False)
        return

    async def send_command_help(self, command):
        command_help = discord.Embed(
            color = self.color,
            title = f'__Command : {command.qualified_name}__',
            description = command.help or 'Help to be given',
            timestamp = self.context.message.created_at
        )
        command_help.set_footer(
            text = self.footer)
        can_run = 'No'
        with contextlib.suppress(commands.CommandError):
            if await command.can_run(self.context):
                can_run = 'Yes'  
        command_help.add_field(
            name = 'Can you use it?', 
            value = f'<:GeraltRightArrow:904740634982760459> {can_run}')
        if command._buckets and (cooldown := command._buckets._cooldown):
            command_help.add_field(
                name = 'Cooldown', 
                value =f'{cooldown.rate} per {cooldown.per:.0f} seconds')
        await self.context.reply(embed = command_help, mention_author = False)
        return

    async def send_group_help(self, group):
        group_embed = discord.Embed(
            color = self.color,
            title = self.get_command_signature(group),
            description = f'{group.help}\n\n',
            timestamp = self.timestamp
        )
        group_embed.set_thumbnail(url=self.context.me.display_avatar.url)
        for command in group.commands:
            group_embed.description += f'<:GeraltRightArrow:904740634982760459> `{command.qualified_name}` - {command.brief}\n'
        can_run = 'No'
        with contextlib.suppress(commands.CommandError):
            if await command.can_run(self.context):
                can_run = 'Yes'
        group_embed.add_field(
            name = 'Can you use it?', 
            value = f'`{can_run}`')
        if command._buckets and (cooldown := command._buckets._cooldown):
            group_embed.add_field(
                name = 'Cooldown', 
                value = f'{cooldown.rate} per {cooldown.per:.0f} seconds')
        await self.context.reply(embed = group_embed, mention_author = False)
        return

    async def send_error_message(self, error):
        help_error = discord.Embed(
            color = self.color,
            title = error,
            timestamp=self.context.message.created_at
        )
        await self.context.reply(embed = help_error, mention_author = False)
        return

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
def setup(bot):
    bot.add_cog(HelpCommand(bot))