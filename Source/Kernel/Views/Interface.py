import typing
import pygit2
import psutil
import dotenv
import discord
import datetime
import itertools
import traceback

from dotenv import dotenv_values
from discord.enums import ButtonStyle
from discord.webhook.async_ import Webhook

import Source.Kernel.Utilities.Flags as FLAGS
from Source.Kernel.Utilities.Crucial import TOTAL_LINES as TL, MISC

dotenv.load_dotenv()

CONFIG  =   dotenv_values(".env")
PAIN    =   "This can't be handled by you at the moment, invoke your very own command <:SarahPray:920484222421045258>"
COLOUR  =   discord.Colour.from_rgb(117, 128, 219)
MENTION =   discord.AllowedMentions.none()

# Gets latest commits from Github and Format them to make it look sexy :D
def Format_Commit(COMMIT):
    short, _, _     = COMMIT.message.partition("\n")
    Commit_Desc     = short[0:40] + "..." if len(short) > 40 else short
    Short_Hash      = COMMIT.hex[0:6]
    Timezone        = datetime.timezone(datetime.timedelta(minutes = COMMIT.commit_time_offset))
    Commit_Time     = datetime.datetime.fromtimestamp(COMMIT.commit_time).astimezone(Timezone)
    Timestamp       = discord.utils.format_dt(Commit_Time, style = "R")
    return f"<:GeraltRightArrow:904740634982760459> [`{Short_Hash}`] : [**{Commit_Desc}**](<https://github.com/BSOD2528/Geralt/commit/{COMMIT.hex}>) - [ {Timestamp} ]"

def Latest_Commit(MAX : int = 5):
    Repository    = pygit2.Repository(".git")
    Commits = list(itertools.islice(Repository.walk(Repository.head.target, pygit2.GIT_SORT_TOPOLOGICAL), MAX))
    return "\n".join(Format_Commit(C) for C in Commits)

# Sub - Class for " Bot Info " command.
# A huge shoutout and thanks to Zeus432 [ Github User ID ] for the amazing idea of adding these buttons :D
class Info(discord.ui.View):
    def __init__(self, bot, ctx):
        super().__init__(timeout = None)
        self.bot = bot
        self.ctx = ctx
        self.Timestamp  = discord.utils.utcnow()
        self.add_item(discord.ui.Button(label = "Dashboard", emoji = "<:AkkoComfy:907104936368685106>", url = "https://bsod2528.github.io/Posts/Geralt"))

    # Misc. Stats like No. of lines, functions and classes.
    @discord.ui.button(label = "Misc.", style = ButtonStyle.blurple, emoji = "<a:WumpusVibe:905457020575031358>", custom_id = "Stats")
    async def STATS(self, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
        Time    =   discord.utils.utcnow()
        STATS_EMB   =   discord.Embed(
            title = "<:VerifiedDev:905668791831265290> Miscellaneous Statistics :",
            description =   f"\n> **Shows Code Related Things :**\n" \
                            f"```prolog\n- Total Classes   : {await MISC('Source/', '.py', 'class'):,}" \
                            f"\n- Total Functions : {await MISC('Source/', '.py', 'def'):,}"
                            f"\n- Total Lines     : {await TL('Source', '.py'):,}```",
            colour = COLOUR)
        await INTERACTION.response.send_message(embed = STATS_EMB, ephemeral = True)
        
    # Shows System Usage at the current moment.
    @discord.ui.button(label = "System Info", style = ButtonStyle.blurple, emoji = "<a:Info:905750331789561856>", custom_id = "Usage")
    async def SYS_USAGE(self, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
        # defer discord
        await INTERACTION.response.defer(ephemeral = True, with_message=True)
        Core_Count  =   psutil.cpu_count()
        CPU_Usage   =   psutil.cpu_percent()
        Mem_Per     =   psutil.virtual_memory().percent
        Mem_GB      =   psutil.virtual_memory().available / 1024 ** 3
        RAM_Usage   =   psutil.Process().memory_full_info().uss / 1024 ** 2

        SYS_USAGE   =   discord.Embed(
            title = "<:WinCogs:898591890209910854> System Usage :",
            description =   f"```prolog\n> CPU Used          : {CPU_Usage:.2f} %\n" \
                            f"> CPU Core Count    : {Core_Count} Cores\n" \
                            f"> Memory Used       : {RAM_Usage:.2f} Megabytes\n" \
                            f"> Memory Available  : {Mem_GB:.3f} GB [ {Mem_Per} % ]\n```",
            colour = COLOUR)
        SYS_USAGE.timestamp =   self.Timestamp
        # send here
        await INTERACTION.followup.send(embed = SYS_USAGE, ephemeral = True)
    
    # Get latest Github commits
    @discord.ui.button(label = "Github Commits", style = ButtonStyle.blurple, emoji = "<a:WumpusHypesquad:905661121501990923>", custom_id = "Commits")
    async def COMMITS(self, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
        COMMIT_EMB  =   discord.Embed(
            title = "<:WinGIT:898591166864441345> My Latest Changes :",
            description = f"**[Github](<https://github.com/BSOD2528/Geralt>)** repository if you want to check things out <:verykewl:916903265541689445> \n\n>>> {Latest_Commit(MAX = 5)}",
            colour = COLOUR)
        COMMIT_EMB.timestamp = self.Timestamp
        COMMIT_EMB.set_footer(text = "If the link is throwing an error, it means commit has to be pushed.")
        await INTERACTION.response.send_message(embed = COMMIT_EMB, ephemeral = True)
    
# Sub - Class for Confirmation based commands which utilises buttons.
class Confirmation(discord.ui.View):
    def __init__(self, YES, NO):
        super().__init__()
        self.Yes        =   YES
        self.No         =   NO

    @discord.ui.button(label = "Yes", style = ButtonStyle.blurple, emoji = "<:WinCheck:898572324490604605>")
    async def YES(self, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
        await self.Yes(self, BUTTON,  INTERACTION)
    
    @discord.ui.button(label = "No", style = ButtonStyle.danger, emoji = "<:WinUncheck:898572376147623956> ")
    async def NO(self, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
        await self.No(self, BUTTON,  INTERACTION)   

#Sub - Classes for User PFP
class PFP(discord.ui.View):
    def __init__(self, bot, ctx, USER : discord.User):
        super().__init__(timeout = 20)
        self.ctx    =   ctx
        self.bot    =   bot
        self.USER   =   USER

    @discord.ui.button(label = "JPG", style = ButtonStyle.gray, emoji = "<:ImageIcon:933966387477630996>")
    async def JPG(self, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
        USER    =   self.USER 
        BUTTON.disabled =   True
        await INTERACTION.message.edit(view = self)
        await INTERACTION.response.send_message(f"Download it as a [**JPG**](<{USER.display_avatar.with_static_format('jpg')}>)", ephemeral = True)
    
    @discord.ui.button(label = "PNG", style = ButtonStyle.gray, emoji = "<:ImageIcon:933966387477630996>")
    async def PNG(self, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
        USER    =   self.USER
        BUTTON.disabled =   True
        await INTERACTION.message.edit(view = self)
        await INTERACTION.response.send_message(f"Download it as a [**PNG**](<{USER.display_avatar.with_static_format('png')}>)", ephemeral = True)
    
    @discord.ui.button(label = "WEBP", style = ButtonStyle.gray, emoji = "<:ImageIcon:933966387477630996>")
    async def WEBP(self, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
        USER    =   self.USER
        BUTTON.disabled =   True
        await INTERACTION.message.edit(view = self)
        await INTERACTION.response.send_message(f"Download it as a [**WEBP**](<{USER.display_avatar.with_static_format('webp')}>)", ephemeral = True)
    
    async def interaction_check(self, INTERACTION : discord.Interaction) -> bool:
        if INTERACTION.user == self.ctx.author:
            return True
        await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True)
    
    async def on_timeout(self) -> None:
        for View in self.children:
            View.disabled   =   True
            await self.message.edit(view = self)

    async def SEND(self, ctx):
        PFP_EMB =   discord.Embed(
            title   =   f"{str(self.USER)}'s Avatar",
            url =   self.USER.display_avatar.url,
            colour = self.bot.colour)
        AVATAR  = self.USER.display_avatar.with_static_format("png")
        PFP_EMB.set_image(url = AVATAR)
        PFP_EMB.timestamp = discord.utils.utcnow()
        self.message    =   await ctx.reply(embed = PFP_EMB , view = self, mention_author = False)

# Error - Handler View
class Traceback(discord.ui.View):
    def __init__(self, bot, ctx, error):
        super().__init__(timeout = 30)
        self.bot    =   bot
        self.ctx    =   ctx
        self.ERROR  =   error
        self.Footer     =   "Click on the buttons for info."  

    @discord.ui.button(label = "Traceback", style = ButtonStyle.blurple, emoji = "<:WinTerminal:898609124982554635>")
    async def Error(self, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
        BUTTON.disabled = True
        BUTTON.style    =   ButtonStyle.green
        ERROR   =   getattr(self.ERROR, "original", self.ERROR)
        ERROR_EMB   =   discord.Embed(
            title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {self.ctx.command}",
            description = f"```yaml\n Quick Tip : Read the last 2 - 3 lines for proper info.\n```\n```py\n {''.join(traceback.format_exception(type(ERROR), ERROR, ERROR.__traceback__))}\n```\n",   
            colour = 0x2F3136)
        await INTERACTION.message.edit(view = self)
        await INTERACTION.response.send_message(embed = ERROR_EMB, ephemeral = True)    
    
    @discord.ui.button(label = "Command Help", style = ButtonStyle.blurple, emoji = "<a:Trash:906004182463569961>")
    async def Help(self, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
        BUTTON.disabled = True
        BUTTON.style    =   ButtonStyle.green
        COMMAND_HELP    =   discord.Embed(
            title   =   f"<:GeraltRightArrow:904740634982760459> Command Help : {self.ctx.command}",
            description =   f"> {self.ctx.command.help}",
            colour  =    0x2F3136)
        COMMAND_HELP.timestamp  =   discord.utils.utcnow()
        COMMAND_HELP.set_footer(text = f"Invoked by {INTERACTION.author}", icon_url = INTERACTION.author.display_avatar.url)
        await INTERACTION.message.edit(view = self)
        await INTERACTION.response.send_message(embed = COMMAND_HELP, ephemeral = True)
    
    async def SEND(self, ctx):
        COMMON_ERROR    =   discord.Embed(
                title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {ctx.command}",
                description = f"```prolog\n {self.ERROR} \n```",
                colour = 0x2F3136)    
        self.message    =   await ctx.reply(embed = COMMON_ERROR, view = self, mention_author = False)

    async def on_timeout(self) -> None:
        for View in self.children:
            View.disabled   =   True
            await self.message.edit(view = self)

    async def interaction_check(self, INTERACTION : discord.Interaction) -> bool:
            if INTERACTION.user == self.ctx.author:
                return True
            await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True)

# Error - Handler View for commands.BadArgumemt
class CommandSyntax(discord.ui.View):
    def __init__(self, bot, ctx, error):
        super().__init__(timeout = 30)
        self.bot    =   bot
        self.ctx    =   ctx
        self.ERROR  =   error
        self.Footer     =   "Click on the buttons for info."  

    @discord.ui.button(label = "Syntax", style = ButtonStyle.blurple, emoji = "<a:CoffeeSip:907110027951742996>")
    async def Syntax(self, BUTTON : discord.ui.Button, INTERACTION : discord.Interaction, disabled = False):
        BUTTON.disabled =   True
        BUTTON.style    =   ButtonStyle.green
        COMMAND_NAME = f"{self.ctx.clean_prefix}{self.ctx.command} {self.ctx.command.signature}"
        SYNTAX_EMB  =   discord.Embed(
            title   =   f"<:GeraltRightArrow:904740634982760459> COMMAND SYNTAX : {self.ctx.clean_prefix}{self.ctx.command}",
            description =   f"\n```prolog\n{COMMAND_NAME}" \
                            f"\n{' ' * (len([item[::-1] for item in COMMAND_NAME[::-1].split(self.ERROR.param.name[::-1], 1)][::-1][0]) - 1)}{'-' * (len(self.ERROR.param.name) + 2)}" \
                            f"\n{self.ERROR.param.name} is a required argument which you have not passed\n```",
            colour  =   0x2F3136)
        SYNTAX_EMB.timestamp    =   discord.utils.utcnow()
        SYNTAX_EMB.set_footer(text = f"Run {self.ctx.clean_prefix}{self.ctx.command} help for more help")
        await INTERACTION.message.edit(view = self)
        await INTERACTION.response.send_message(embed = SYNTAX_EMB, ephemeral = True)

    @discord.ui.button(label = "Traceback", style = ButtonStyle.blurple, emoji = "<:WinTerminal:898609124982554635>")
    async def Error(self, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
        BUTTON.disabled = True
        BUTTON.style    =   ButtonStyle.green
        ERROR   =   getattr(self.ERROR, "original", self.ERROR)
        ERROR_EMB   =   discord.Embed(
            title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {self.ctx.command}",
            description = f"```yaml\n Quick Tip : Read the last 2 - 3 lines for proper info.\n```\n```py\n {''.join(traceback.format_exception(type(ERROR), ERROR, ERROR.__traceback__))}\n```\n",   
            colour = 0x2F3136)
        await INTERACTION.message.edit(view = self)
        await INTERACTION.response.send_message(embed = ERROR_EMB, ephemeral = True)    

    @discord.ui.button(label = "Command Help", style = ButtonStyle.blurple, emoji = "<a:Trash:906004182463569961>")
    async def Help(self, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
        BUTTON.disabled =   True
        BUTTON.style    =   ButtonStyle.green
        COMMAND_HELP    =   discord.Embed(
            title   =   f"<:GeraltRightArrow:904740634982760459> Command Help : {self.ctx.command}",
            description =   f"> {self.ctx.command.help}",
            colour  =    0x2F3136)
        COMMAND_HELP.timestamp  =   discord.utils.utcnow()
        COMMAND_HELP.set_footer(text = f"Invoked by {INTERACTION.author}", icon_url = INTERACTION.author.display_avatar.url)
        await INTERACTION.message.edit(view = self)
        await INTERACTION.response.send_message(embed = COMMAND_HELP, ephemeral = True)
    
    async def SEND(self, ctx):
        COMMON_ERROR    =   discord.Embed(
                title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {ctx.command}",
                description = f"```prolog\n {self.ERROR} \n```\nClick on the `Syntax` Button for the proper syntax of `{self.ctx.command}`",
                colour = 0x2F3136)  
        COMMON_ERROR.timestamp  =   discord.utils.utcnow()
        COMMON_ERROR.set_footer(text = f"Errored by {ctx.author}", icon_url = ctx.author.display_avatar.url)  
        self.message    =   await ctx.reply(embed = COMMON_ERROR, view = self, mention_author = False)

    async def on_timeout(self) -> None:
        for View in self.children:
            View.disabled   =   True
            await self.message.edit(view = self)

    async def interaction_check(self, INTERACTION : discord.Interaction) -> bool:
            if INTERACTION.user == self.ctx.author:
                return True
            await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True)

# Nitro Command View
class Nitro(discord.ui.View):
    def __init__(self, USER : discord.Member = None):
        super().__init__()

    @discord.ui.button(label = "Avail Nitro", style = ButtonStyle.green, emoji = "<a:WumpusHypesquad:905661121501990923>")
    async def Nitro(self, BUTTON : discord.ui.Button, INTERACTION : discord.Interaction):
        BUTTON.disabled =   True
        BUTTON.label    =   "Claimed"
        await INTERACTION.message.edit(view = self)
        await INTERACTION.user.send(content = f"discord.gift/R1cKr0OlL3d")
        await INTERACTION.response.send_message(content = "https://imgur.com/NQinKJB", ephemeral = True)     

# Classes for Pop Game
class PopButton(discord.ui.Button):
    async def callback(self, INTERACTION : discord.Interaction):
        await INTERACTION.response.defer()
        self.disabled   =   True
        self.style      =   ButtonStyle.grey
        await self.view.message.edit(view = self.view)
    
class Pop(discord.ui.View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx        =   ctx
        self.message    :   typing.Optional[discord.Message]   =   None
    
    async def start(self):
        for BUTTON in range(5):
            self.add_item(PopButton(label = "\u200b", style = ButtonStyle.blurple))
        self.message    =   await self.ctx.send("\u200b", view = self)
    
    async def interaction_check(self, INTERACTION : discord.Interaction) -> bool:
            if INTERACTION.user == self.ctx.author:
                return True
            await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True)

class PopMedium(discord.ui.View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx        =   ctx
        self.message    :   typing.Optional[discord.Message]   =   None
    
    async def start(self):
        for BUTTON in range(10):
            self.add_item(PopButton(label = "\u200b", style = ButtonStyle.blurple))
        self.message    =   await self.ctx.send("\u200b", view = self)
    
    async def interaction_check(self, INTERACTION : discord.Interaction) -> bool:
            if INTERACTION.user == self.ctx.author:
                return True
            await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True) 
    
class PopLarge(discord.ui.View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx        =   ctx
        self.message    :   typing.Optional[discord.Message]   =   None
    
    async def start(self):
        for BUTTON in range(20):
            self.add_item(PopButton(label = "\u200b", style = ButtonStyle.blurple))
        self.message    =   await self.ctx.send("\u200b", view = self)
    
    async def interaction_check(self, INTERACTION : discord.Interaction) -> bool:
            if INTERACTION.user == self.ctx.author:
                return True
            await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True)  