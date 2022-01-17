import pygit2
import psutil
import discord
import datetime
import itertools

from discord.ext import commands
from discord.enums import ButtonStyle

from Core.Kernel.Utilities.Essential import TOTAL_LINES as TL
from Core.Kernel.Utilities.Essential import MISC

PAIN    =   "This can't be handled by you at the moment, invoke your very own command <:SarahPray:920484222421045258>"
COLOUR  =   discord.Colour.from_rgb(117, 128, 219)

# Gets latest commits from Github and Format them to make it look sexy :D
def Format_Commit(COMMIT):
    short, _, _     = COMMIT.message.partition("\n")
    Commit_Desc     = short[0:40] + "..." if len(short) > 40 else short
    Short_Hash      = COMMIT.hex[0:6]
    Timezone        = datetime.timezone(datetime.timedelta(minutes = COMMIT.commit_time_offset))
    Commit_Time     = datetime.datetime.fromtimestamp(COMMIT.commit_time).astimezone(Timezone)
    Timestamp       = discord.utils.format_dt(Commit_Time, style = "R")
    return f"<:GeraltRightArrow:904740634982760459> [**`{Short_Hash}`**](<https://github.com/BSOD2528/Geralt/commit/{COMMIT.hex}>) **: {Commit_Desc} -** [ {Timestamp} ]"

def Latest_Commit(MAX : int = 5):
    Repository    = pygit2.Repository(".git")
    Commits = list(itertools.islice(Repository.walk(Repository.head.target, pygit2.GIT_SORT_TOPOLOGICAL), MAX))
    return "\n".join(Format_Commit(C) for C in Commits)

# Sub - Class for " Bot Info " command.
# A huge shoutout and thanks to Zeus432 [ Github User ID ] for the amazing idea of adding these buttons :D
class Info(discord.ui.View):
    def __init__(self, ctx, bot):
        super().__init__()
        self.ctx = ctx
        self.bot = bot
        self.Timestamp  =   datetime.datetime.now(datetime.timezone.utc)

    # Misc. Stats like No. of lines, functions and classes.
    @discord.ui.button(label = "Misc.", style = ButtonStyle.blurple, emoji = "<a:WumpusVibe:905457020575031358>")
    async def STATS(self, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
        Time    =   discord.utils.utcnow()
        STATS_EMB   =   discord.Embed(
            title = "<:VerifiedDev:905668791831265290> Miscellaneous Statistics :",
            description =   f"\n**Been Up Since :** {discord.utils.format_dt(Time, style = 'D')}"
                            f"```yaml\n- Total Classes   : {await MISC('Core/', '.py', 'class'):,}" \
                            f"\n- Total Functions : {await MISC('Core/', '.py', 'def'):,}"
                            f"\n- Total Lines     : {await TL('Core', '.py'):,}```",
            colour = COLOUR)
        await INTERACTION.response.send_message(embed = STATS_EMB, ephemeral = True)
        
    # Shows System Usage at the current moment.
    @discord.ui.button(label = "System Info", style = ButtonStyle.blurple, emoji = "<a:Info:905750331789561856>")
    async def SYS_USAGE(self, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
        Core_Count  =   psutil.cpu_count()
        CPU_Usage   =   psutil.cpu_percent()
        Mem_Per     =   psutil.virtual_memory().percent
        Mem_GB      =   psutil.virtual_memory().available / 1024 ** 3
        RAM_Usage   =   psutil.Process().memory_full_info().uss / 1024 ** 2

        SYS_USAGE   =   discord.Embed(
            title = "<:WinCogs:898591890209910854> System Usage :",
            description =   f"```yaml\n> CPU Used          : {CPU_Usage:.2f} %\n" \
                            f"> CPU Core Count    : {Core_Count} Cores\n" \
                            f"> Memory Used       : {RAM_Usage:.2f} Megabytes\n" \
                            f"> Memory Available  : {Mem_GB:.3f} GB [ {Mem_Per} % ]\n" \
                            f"> Operating System  : Windows 10 Pro 10.0.19042\n```",
            colour = COLOUR)
        SYS_USAGE.timestamp =   self.Timestamp
        await INTERACTION.response.send_message(embed = SYS_USAGE, ephemeral = True)
    
    # Get latest Github commits
    @discord.ui.button(label = "Github Commits", style = ButtonStyle.blurple, emoji = "<a:WumpusHypesquad:905661121501990923>")
    async def COMMITS(self, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
        COMMIT_EMB  =   discord.Embed(
            title = "<:WinGIT:898591166864441345> My Latest Changes :",
            description = f"**[Github](<https://github.com/BSOD2528/Geralt>)** repository if you want to check things out <:verykewl:916903265541689445> \n\n>>> {Latest_Commit(MAX = 5)}",
            colour = COLOUR)
        COMMIT_EMB.timestamp = self.Timestamp
        await INTERACTION.response.send_message(embed = COMMIT_EMB, ephemeral = True)
    
    # Delete the entire message
    @discord.ui.button(label = "Delete", style = ButtonStyle.danger, emoji = "<a:Trash:906004182463569961>")
    async def DELETE(self, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
        await INTERACTION.response.send_message("Deleting the whole message as you wish", ephemeral = True)
        await INTERACTION.message.delete()
   
    async def interaction_check(self, INTERACTION : discord.Interaction) -> bool:
        if INTERACTION.user == self.ctx.author:
            return True
        await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True)

# Sub - Class for Confirmation based commands which utilises buttons.
class Confirmation(discord.ui.View):
    def __init__(self, Yes, No):
        super().__init__()
        self.Yes    = Yes
        self.No     = No
    
    @discord.ui.button(label = "Yes", style = ButtonStyle.blurple, emoji = "<:WinCheck:898572324490604605>")
    async def YES(self, BUTTON : discord.ui.Button, INTERACTION : discord.Interaction):
        await self.Yes(self, BUTTON,  INTERACTION)
    
    @discord.ui.button(label = "No", style = ButtonStyle.danger, emoji = "<:WinUncheck:898572376147623956> ")
    async def NO(self, BUTTON : discord.ui.Button, INTERACTION : discord.Interaction):
        await self.No(self, BUTTON,  INTERACTION)   