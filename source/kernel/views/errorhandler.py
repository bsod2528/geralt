import discord
import traceback

from ..subclasses.bot import Geralt
from ..subclasses.embed import BaseEmbed
from ..subclasses.context import GeraltContext

# Error - Handler View
class Traceback(discord.ui.View):
    def __init__(self, bot : Geralt, ctx : GeraltContext, error):
        super().__init__(timeout = 60)
        self.bot : Geralt = bot
        self.ctx : GeraltContext = ctx
        self.error = error

    @discord.ui.button(label = "Traceback", style = discord.ButtonStyle.blurple, emoji = "<:WinTerminal:898609124982554635>", custom_id = "traceback-traceback")
    async def traceback(self, interaction : discord.Interaction, button : discord.ui.Button):
        button.disabled = True
        button.style = discord.ButtonStyle.green
        error = getattr(self.error, "original", self.error)
        error_emb = BaseEmbed(
            title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {self.ctx.command}",
            description = f"```yaml\n Quick Tip : Read the last 2 - 3 lines for proper info.\n```\n```py\n {''.join(traceback.format_exception(type(error), error, error.__traceback__))}\n```\n",   
            colour = 0x2F3136)
        await interaction.message.edit(view = self)
        await interaction.response.send_message(embed = error_emb, ephemeral = True)    
    
    @discord.ui.button(label = "Command Help", style = discord.ButtonStyle.blurple, emoji = "<a:Trash:906004182463569961>", custom_id = "traceback-command-help")
    async def cmd_help(self, interaction : discord.Interaction, button : discord.ui.Button):
        button.disabled = True
        button.style = discord.ButtonStyle.green
        command_help = BaseEmbed(
            title = f"<:GeraltRightArrow:904740634982760459> Command Help : {self.ctx.command}",
            description = f"> {self.ctx.command.help}",
            colour = 0x2F3136)
        command_help.set_footer(text = f"Invoked by {interaction.user}", icon_url = interaction.user.display_avatar.url)
        await interaction.message.edit(view = self)
        await interaction.response.send_message(embed = command_help, ephemeral = True)
    
    @discord.ui.button(label = "Delete", style = discord.ButtonStyle.red, emoji = "<a:Trash:906004182463569961>", custom_id = "traceback-delete")
    async def delete(self, interaction : discord.Interaction, button : discord.ui.Button):
        await interaction.message.delete()

    async def send(self):
        common_error = BaseEmbed(
                title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {self.ctx.command}",
                description = f"```py\n{self.error}\n```",
                colour = 0x2F3136)    
        common_error.timestamp = discord.utils.utcnow()
        common_error.set_footer(text = f"Errored by {self.ctx.author}", icon_url = self.ctx.author.display_avatar.url)  
        self.message = await self.ctx.reply(embed = common_error, view = self, mention_author = False)
        return self.message

    async def on_timeout(self) -> None:
        try:
            for view in self.children:
                view.disabled = True
                await self.message.edit(view = self)
        except discord.errors.NotFound:
            pass

    async def interaction_check(self, interaction : discord.Interaction) -> bool:
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{self.ctx.clean_prefix}{self.ctx.command}` for the `{self.ctx.command}` command <:SarahPray:920484222421045258>"
        if interaction.user == self.ctx.author:
            return True
        await interaction.response.send_message(content = f"{pain}", ephemeral = True)

# Error - Handler View for commands.BadArgumemt
class CommandSyntax(discord.ui.View):
    def __init__(self, bot : Geralt, ctx : GeraltContext, error):
        super().__init__(timeout = 60)
        self.bot = bot
        self.ctx = ctx
        self.error = error

    @discord.ui.button(label = "Syntax", style = discord.ButtonStyle.blurple, emoji = "<a:CoffeeSip:907110027951742996>", custom_id = "commandsyntax-syntax")
    async def cmd_syntax(self, interaction : discord.Interaction, button : discord.ui.Button):
        button.disabled = True
        button.style = discord.ButtonStyle.green
        try:
            command_name = f"{self.ctx.clean_prefix}{self.ctx.command} {self.ctx.command.signature}"
            syntax_emb = BaseEmbed(
                title = f"<:GeraltRightArrow:904740634982760459> COMMAND SYNTAX : {self.ctx.clean_prefix}{self.ctx.command}",
                description = f"\n```prolog\n{command_name}" \
                          f"\n{' ' * (len([item[::-1] for item in command_name[::-1].split(self.error.param.name[::-1], 1)][::-1][0]) - 1)}{'-' * (len(self.error.param.name) + 2)}" \
                          f"\n\"{self.error.param.name}\" is a required argument which you have not passed\n```",
                colour = 0x2F3136)
            syntax_emb.set_footer(text = f"Run {self.ctx.clean_prefix}{self.ctx.command} help for more help")
            await interaction.message.edit(view = self)
            await interaction.response.send_message(embed = syntax_emb, ephemeral = True)
        except:
            await interaction.response.send_message(content = f"This command does not have any argument missing. Rather a wrong argument was passed. Run `{self.ctx.clean_prefix}help {self.ctx.command}`", ephemeral = True)    

    @discord.ui.button(label = "Command Help", style = discord.ButtonStyle.blurple, emoji = "<a:Trash:906004182463569961>", custom_id = "commandsyntax-command-help")
    async def cmd_help(self, interaction : discord.Interaction, button : discord.ui.Button):
        button.disabled = True
        button.style = discord.ButtonStyle.green
        command_help = BaseEmbed(
            title = f"<:GeraltRightArrow:904740634982760459> Command Help : {self.ctx.command}",
            description = f"> {self.ctx.command.help}",
            colour = 0x2F3136)
        command_help.set_footer(text = f"Invoked by {interaction.user}", icon_url = interaction.user.display_avatar.url)
        await interaction.message.edit(view = self)
        try:
            await interaction.response.send_message(embed = command_help, ephemeral = True)
        except Exception as exception:
            await interaction.response.send_message(content = exception, ephemeral = True)    

    @discord.ui.button(label = "Traceback", style = discord.ButtonStyle.blurple, emoji = "<:WinTerminal:898609124982554635>", custom_id = "commandsyntax-traceback")
    async def traceback(self, interaction : discord.Interaction, button : discord.ui.Button):
        button.disabled = True
        button.style = discord.ButtonStyle.green
        error = getattr(self.error, "original", self.error)
        error_emb = BaseEmbed(
            title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {self.ctx.command}",
            description = f"```yaml\n Quick Tip : Read the last 2 - 3 lines for proper info.\n```\n```py\n {''.join(traceback.format_exception(type(error), error, error.__traceback__))}\n```\n",   
            colour = 0x2F3136)
        await interaction.message.edit(view = self)
        try:
            await interaction.response.send_message(embed = error_emb, ephemeral = True)    
        except Exception as exception:
            await interaction.response.send_message(content = exception, ephemeral = True)    
    
    @discord.ui.button(label = "Delete", style = discord.ButtonStyle.red, emoji = "<a:Trash:906004182463569961>", custom_id = "commandsyntax-delete")
    async def delete(self, interaction : discord.Interaction, button : discord.ui.Button):
        await interaction.message.delete()

    async def send(self):
        common_error = BaseEmbed(
                title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {self.ctx.command}",
                description = f"```py\n{self.error}\n```\nClick on the `Syntax` Button for the proper syntax of `{self.ctx.command}`",
                colour = 0x2F3136)  
        common_error.set_footer(text = f"Errored by {self.ctx.author}", icon_url = self.ctx.author.display_avatar.url)  
        self.message = await self.ctx.reply(embed = common_error, view = self, mention_author = False)
        return self.message

    async def on_timeout(self) -> None:
        try:
            for view in self.children:
                view.disabled = True
                await self.message.edit(view = self)
        except discord.errors.NotFound:
            pass
        
    async def interaction_check(self, interaction : discord.Interaction) -> bool:
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{self.ctx.clean_prefix}{self.ctx.command}` for the `{self.ctx.command}` command <:SarahPray:920484222421045258>"
        if interaction.user == self.ctx.author:
            return True
        await interaction.response.send_message(content = f"{pain}", ephemeral = True)