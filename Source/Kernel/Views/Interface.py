import typing
import pygit2
import psutil
import dotenv
import discord
import datetime
import itertools
import traceback

from discord.ext import commands
from dotenv import dotenv_values
from discord.enums import ButtonStyle

from Source.Kernel.Utilities.Crucial import total_lines as tl, misc
dotenv.load_dotenv()

CONFIG  =   dotenv_values(".env")
COLOUR  =   discord.Colour.from_rgb(117, 128, 219)
MENTION =   discord.AllowedMentions.none()

# Gets latest commits from Github and Format them to make it look sexy :D
def Format_Commit(commit):
    short, _, _ = commit.message.partition("\n")
    commit_desc = short[0:40] + "..." if len(short) > 40 else short
    short_hash = commit.hex[0:6]
    timezone = datetime.timezone(datetime.timedelta(minutes = commit.commit_time_offset))
    commit_time = datetime.datetime.fromtimestamp(commit.commit_time).astimezone(timezone)
    timestamp = discord.utils.format_dt(commit_time, style = "R")
    return f"<:GeraltRightArrow:904740634982760459> [` {short_hash} `] : [**{commit_desc}**](<https://github.com/BSOD2528/Geralt/commit/{commit.hex}>) - [ {timestamp} ]"

def Latest_Commit(MAX : int = 5):
    Repository = pygit2.Repository(".git")
    Commits = list(itertools.islice(Repository.walk(Repository.head.target, pygit2.GIT_SORT_TOPOLOGICAL), MAX))
    return "\n".join(Format_Commit(C) for C in Commits)

# Sub - Class for " Bot Info " command.
# A huge shoutout and thanks to Zeus432 [ Github User ID ] for the amazing idea of adding these buttons :D
class Info(discord.ui.View):
    def __init__(self, bot, ctx):
        super().__init__(timeout = None)
        self.bot = bot
        self.ctx = ctx
        self.add_item(discord.ui.Button(label = "Dashboard", emoji = "<:AkkoComfy:907104936368685106>", url = "https://bsod2528.github.io/Posts/Geralt"))

    # Misc. Stats like No. of lines, functions and classes.
    @discord.ui.button(label = "Misc.", style = ButtonStyle.blurple, emoji = "<a:WumpusVibe:905457020575031358>", custom_id = "Stats")
    async def stats(self, interaction : discord.Interaction, button : discord.ui.button):
        stats_emb = discord.Embed(
            title = "<:VerifiedDev:905668791831265290> Miscellaneous Statistics :",
            description = f"\n Shows Code Related Things :\n" \
                          f"```prolog\n- Total Classes   : {await misc('Source/', '.py', 'class'):,}" \
                          f"\n- Total Functions : {await misc('Source/', '.py', 'def'):,}"
                          f"\n- Total Lines     : {await tl('Source', '.py'):,}```",
            colour = COLOUR)
        await interaction.response.send_message(embed = stats_emb, ephemeral = True)
        
    # Shows System Usage at the current moment.
    @discord.ui.button(label = "System Info", style = ButtonStyle.blurple, emoji = "<a:Info:905750331789561856>", custom_id = "Usage")
    async def sys_usage(self, interaction : discord.Interaction, button : discord.ui.button):
        core_count = psutil.cpu_count()
        cpu_usage = psutil.cpu_percent()
        mem_per = psutil.virtual_memory().percent
        mem_gb = psutil.virtual_memory().available / 1024 ** 3
        ram_usage = psutil.Process().memory_full_info().uss / 1024 ** 2

        sys_usage_emb = discord.Embed(
            title = "<:WinCogs:898591890209910854> System Usage :",
            description = f"```prolog\n> CPU Used          : {cpu_usage:.2f} %\n" \
                          f"> CPU Core Count    : {core_count} Cores\n" \
                          f"> Memory Used       : {ram_usage:.2f} Megabytes\n" \
                          f"> Memory Available  : {mem_gb:.3f} GB [ {mem_per} % ]\n```",
            colour = COLOUR)
        sys_usage_emb.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed = sys_usage_emb, ephemeral = True)
    
    # Get latest Github commits
    @discord.ui.button(label = "Github Commits", style = ButtonStyle.blurple, emoji = "<a:WumpusHypesquad:905661121501990923>", custom_id = "Commits")
    async def commits(self, interaction : discord.Interaction, button : discord.ui.button):
        commit_emb = discord.Embed(
            title = "<:WinGIT:898591166864441345> My Latest Changes :",
            description = f"**[Github](<https://github.com/BSOD2528/Geralt>)** repository if you want to check things out <:verykewl:916903265541689445> \n\n>>> {Latest_Commit(MAX = 5)}",
            colour = COLOUR)
        commit_emb.timestamp = discord.utils.utcnow()
        commit_emb.set_footer(text = "If the link is throwing an error, it means commit has to be pushed.")
        await interaction.response.send_message(embed = commit_emb, ephemeral = True)
    
# Sub - Class for Confirmation based commands which utilises buttons.
class Confirmation(discord.ui.View):
    def __init__(self, ctx,yes, no):
        super().__init__()
        self.ctx = ctx
        self.yes = yes
        self.no = no

    @discord.ui.button(label = "Yes", style = ButtonStyle.blurple, emoji = "<:WinCheck:898572324490604605>")
    async def confirmed(self, interaction : discord.Interaction, button : discord.ui.button):
        await self.yes(self, interaction, button)
    
    @discord.ui.button(label = "No", style = ButtonStyle.danger, emoji = "<:WinUncheck:898572376147623956> ")
    async def cancelled(self, interaction : discord.Interaction, button : discord.ui.button):
        await self.no(self, interaction, button)   
        
#Sub - Classes for User PFP
class PFP(discord.ui.View):
    def __init__(self, bot, ctx : commands.context, user : discord.User):
        super().__init__(timeout = 60)
        self.ctx = ctx
        self.bot = bot
        self.user = user

    @discord.ui.button(label = "JPG", style = ButtonStyle.gray, emoji = "<:ImageIcon:933966387477630996>")
    async def jpg(self, interaction : discord.Interaction, button : discord.ui.button):
        user = self.user 
        button.disabled = True
        await interaction.message.edit(view = self)
        await interaction.response.send_message(f"Download it as a [**JPG**](<{user.display_avatar.with_static_format('jpg')}>)", ephemeral = True)
    
    @discord.ui.button(label = "PNG", style = ButtonStyle.gray, emoji = "<:ImageIcon:933966387477630996>")
    async def png(self, interaction : discord.Interaction, button : discord.ui.button):
        user = self.user
        button.disabled = True
        await interaction.message.edit(view = self)
        await interaction.response.send_message(f"Download it as a [**PNG**](<{user.display_avatar.with_static_format('png')}>)", ephemeral = True)
    
    @discord.ui.button(label = "WEBP", style = ButtonStyle.gray, emoji = "<:ImageIcon:933966387477630996>")
    async def webp(self, interaction : discord.Interaction, button : discord.ui.button):
        user = self.user
        button.disabled = True
        await interaction.message.edit(view = self)
        await interaction.response.send_message(f"Download it as a [**WEBP**](<{user.display_avatar.with_static_format('webp')}>)", ephemeral = True)
    
    async def interaction_check(self, interaction : discord.Interaction) -> bool:
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{self.ctx.clean_prefix}{self.ctx.command}` for the `{self.ctx.command}` command <:SarahPray:920484222421045258>"
        if interaction.user == self.ctx.author:
            return True
        await interaction.response.send_message(content = f"{pain}", ephemeral = True)
    
    async def on_timeout(self) -> None:
        for view in self.children:
            view.disabled = True
            await self.message.edit(view = self)

    async def send(self, ctx : commands.context):
        pfp_emb = discord.Embed(
            title = f"{str(self.user)}'s Avatar",
            url = self.user.display_avatar.url,
            colour = self.bot.colour)
        pfp_emb.set_image(url = self.user.display_avatar.with_static_format("png"))
        pfp_emb.timestamp = discord.utils.utcnow()
        self.message = await ctx.reply(embed = pfp_emb , view = self, mention_author = False)

# Error - Handler View
class Traceback(discord.ui.View):
    def __init__(self, bot, ctx, error):
        super().__init__(timeout = 60)
        self.bot = bot
        self.ctx = ctx
        self.error = error

    @discord.ui.button(label = "Traceback", style = ButtonStyle.blurple, emoji = "<:WinTerminal:898609124982554635>")
    async def traceback(self, interaction : discord.Interaction, button : discord.ui.button):
        button.disabled = True
        button.style = ButtonStyle.green
        error = getattr(self.error, "original", self.error)
        error_emb = discord.Embed(
            title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {self.ctx.command}",
            description = f"```yaml\n Quick Tip : Read the last 2 - 3 lines for proper info.\n```\n```py\n {''.join(traceback.format_exception(type(error), error, error.__traceback__))}\n```\n",   
            colour = 0x2F3136)
        await interaction.message.edit(view = self)
        await interaction.response.send_message(embed = error_emb, ephemeral = True)    
    
    @discord.ui.button(label = "Command Help", style = ButtonStyle.blurple, emoji = "<a:Trash:906004182463569961>")
    async def cmd_help(self, interaction : discord.Interaction, button : discord.ui.button):
        button.disabled = True
        button.style = ButtonStyle.green
        command_help = discord.Embed(
            title = f"<:GeraltRightArrow:904740634982760459> Command Help : {self.ctx.command}",
            description = f"> {self.ctx.command.help}",
            colour = 0x2F3136)
        command_help.timestamp = discord.utils.utcnow()
        command_help.set_footer(text = f"Invoked by {interaction.author}", icon_url = interaction.author.display_avatar.url)
        await interaction.message.edit(view = self)
        await interaction.response.send_message(embed = command_help, ephemeral = True)
    
    async def send(self, ctx):
        common_error = discord.Embed(
                title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {ctx.command}",
                description = f"```py\n{self.error}\n```",
                colour = 0x2F3136)    
        common_error.timestamp = discord.utils.utcnow()
        common_error.set_footer(text = f"Errored by {ctx.author}", icon_url = ctx.author.display_avatar.url)  
        self.message = await ctx.reply(embed = common_error, view = self, mention_author = False)

    async def on_timeout(self) -> None:
        for view in self.children:
            view.disabled = True
            await self.message.edit(view = self)

    async def interaction_check(self, interaction : discord.Interaction) -> bool:
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{self.ctx.clean_prefix}{self.ctx.command}` for the `{self.ctx.command}` command <:SarahPray:920484222421045258>"
        if interaction.user == self.ctx.author:
            return True
        await interaction.response.send_message(content = f"{pain}", ephemeral = True)

# Error - Handler View for commands.BadArgumemt
class CommandSyntax(discord.ui.View):
    def __init__(self, bot, ctx, error):
        super().__init__(timeout = 60)
        self.bot = bot
        self.ctx = ctx
        self.error = error

    @discord.ui.button(label = "Syntax", style = ButtonStyle.blurple, emoji = "<a:CoffeeSip:907110027951742996>")
    async def cmd_syntax(self, interaction : discord.Interaction, button : discord.ui.button):
        button.disabled = True
        button.style = ButtonStyle.green
        command_name = f"{self.ctx.clean_prefix}{self.ctx.command} {self.ctx.command.signature}"
        syntax_emb = discord.Embed(
            title = f"<:GeraltRightArrow:904740634982760459> COMMAND SYNTAX : {self.ctx.clean_prefix}{self.ctx.command}",
            description = f"\n```bash\n{command_name}" \
                          f"\n{' ' * (len([item[::-1] for item in command_name[::-1].split(self.error.param.name[::-1], 1)][::-1][0]) - 1)}{'-' * (len(self.error.param.name) + 2)}" \
                          f"\n{self.error.param.name} is a required argument which you have not passed\n```",
            colour = 0x2F3136)
        syntax_emb.timestamp = discord.utils.utcnow()
        syntax_emb.set_footer(text = f"Run {self.ctx.clean_prefix}{self.ctx.command} help for more help")
        await interaction.message.edit(view = self)
        await interaction.response.send_message(embed = syntax_emb, ephemeral = True)

    @discord.ui.button(label = "Command Help", style = ButtonStyle.blurple, emoji = "<a:Trash:906004182463569961>")
    async def cmd_help(self, interaction : discord.Interaction, button : discord.ui.button):
        button.disabled = True
        button.style = ButtonStyle.green
        command_help = discord.Embed(
            title = f"<:GeraltRightArrow:904740634982760459> Command Help : {self.ctx.command}",
            description = f"> {self.ctx.command.help}",
            colour = 0x2F3136)
        command_help.timestamp = discord.utils.utcnow()
        command_help.set_footer(text = f"Invoked by {interaction.user}", icon_url = interaction.author.display_avatar.url)
        await interaction.message.edit(view = self)
        await interaction.response.send_message(embed = command_help, ephemeral = True)

    @discord.ui.button(label = "Traceback", style = ButtonStyle.blurple, emoji = "<:WinTerminal:898609124982554635>")
    async def traceback(self, interaction : discord.Interaction, button : discord.ui.button):
        button.disabled = True
        button.style = ButtonStyle.green
        error = getattr(self.error, "original", self.error)
        error_emb = discord.Embed(
            title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {self.ctx.command}",
            description = f"```yaml\n Quick Tip : Read the last 2 - 3 lines for proper info.\n```\n```py\n {''.join(traceback.format_exception(type(error), error, error.__traceback__))}\n```\n",   
            colour = 0x2F3136)
        await interaction.message.edit(view = self)
        await interaction.response.send_message(embed = error_emb, ephemeral = True)    
    
    async def send(self, ctx):
        common_error = discord.Embed(
                title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {ctx.command}",
                description = f"```py\n {self.error} \n```\nClick on the `Syntax` Button for the proper syntax of `{self.ctx.command}`",
                colour = 0x2F3136)  
        common_error.timestamp  =   discord.utils.utcnow()
        common_error.set_footer(text = f"Errored by {ctx.author}", icon_url = ctx.author.display_avatar.url)  
        self.message = await ctx.reply(embed = common_error, view = self, mention_author = False)

    async def on_timeout(self) -> None:
        for view in self.children:
            view.disabled = True
            await self.message.edit(view = self)

    async def interaction_check(self, interaction : discord.Interaction) -> bool:
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{self.ctx.clean_prefix}{self.ctx.command}` for the `{self.ctx.command}` command <:SarahPray:920484222421045258>"
        if interaction.user == self.ctx.author:
            return True
        await interaction.response.send_message(content = f"{pain}", ephemeral = True)

# Nitro Command View
class Nitro(discord.ui.View):
    def __init__(self, user : discord.Member = None):
        super().__init__()

    @discord.ui.button(label = "Avail Nitro", style = ButtonStyle.green, emoji = "<a:WumpusHypesquad:905661121501990923>")
    async def nitro(self, interaction : discord.Interaction, button : discord.ui.button):
        button.disabled = True
        button.label = "Claimed"
        await interaction.message.edit(view = self)
        await interaction.user.send(content = f"discord.gift/R1cKr0OlL3d")
        await interaction.response.send_message(content = "https://imgur.com/NQinKJB", ephemeral = True)     

# Classes for Pop Game
class PopButton(discord.ui.Button):
    async def callback(self, interaction : discord.Interaction):
        await interaction.response.defer()
        self.disabled = True
        self.style = ButtonStyle.grey
        await self.view.message.edit(view = self.view)
    
class Pop(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout = 90)
        self.ctx = ctx
        self.message : typing.Optional[discord.Message] = None
    
    async def start(self):
        for button in range(5):
            self.add_item(PopButton(label = "\u200b", style = ButtonStyle.blurple))
        self.message = await self.ctx.send("\u200b", view = self)
    
    async def on_timeout(self) -> None:
        for view in self.children:
            view.disabled = True
            view.style = ButtonStyle.grey
            await self.message.edit(view = self)

    async def interaction_check(self, interaction : discord.Interaction) -> bool:
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{self.ctx.clean_prefix}{self.ctx.command}` for the `{self.ctx.command}` command <:SarahPray:920484222421045258>"
        if interaction.user == self.ctx.author:
            return True
        await interaction.response.send_message(content = f"{pain}", ephemeral = True)

class PopMedium(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout = 90)
        self.ctx = ctx
        self.message : typing.Optional[discord.Message] = None
    
    async def start(self):
        for button in range(10):
            self.add_item(PopButton(label = "\u200b", style = ButtonStyle.blurple))
        self.message = await self.ctx.send("\u200b", view = self)
    
    async def on_timeout(self) -> None:
        for view in self.children:
            view.disabled = True
            view.style = ButtonStyle.grey
            await self.message.edit(view = self)

    async def interaction_check(self, interaction : discord.Interaction) -> bool:
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{self.ctx.clean_prefix}{self.ctx.command}` for the `{self.ctx.command}` command <:SarahPray:920484222421045258>"
        if interaction.user == self.ctx.author:
            return True
        await interaction.response.send_message(content = f"{pain}", ephemeral = True) 
    
class PopLarge(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout = 90)
        self.ctx = ctx
        self.message : typing.Optional[discord.Message] = None
    
    async def start(self):
        for button in range(20):
            self.add_item(PopButton(label = "\u200b", style = ButtonStyle.blurple))
        self.message = await self.ctx.send("\u200b", view = self)
    
    async def on_timeout(self) -> None:
        for view in self.children:
            view.disabled = True
            view.style = ButtonStyle.grey
            await self.message.edit(view = self)
    
    async def interaction_check(self, interaction : discord.Interaction) -> bool:
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{self.ctx.clean_prefix}{self.ctx.command}` for the `{self.ctx.command}` command <:SarahPray:920484222421045258>"
        if interaction.user == self.ctx.author:
            return True
        await interaction.response.send_message(content = f"{pain}", ephemeral = True)  