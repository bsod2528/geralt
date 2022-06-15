import pygit2
import psutil
import discord
import datetime
import itertools

from discord.ext import commands

from ..subclasses.context import GeraltContext
from ..utilities.crucial import misc, total_lines as tl, misc

COLOUR = discord.Colour.from_rgb(117, 128, 219)

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
    def __init__(self, bot, ctx : GeraltContext):
        super().__init__(timeout = None)
        self.bot = bot
        self.ctx = ctx
        self.add_item(discord.ui.Button(label = "Dashboard", emoji = "<:AkkoComfy:907104936368685106>", url = "https://bsod2528.github.io/Posts/Geralt"))

    # Misc. Stats like No. of lines, functions and classes.
    @discord.ui.button(label = "Misc.", style = discord.ButtonStyle.blurple, emoji = "<a:WumpusVibe:905457020575031358>", custom_id = "Stats")
    async def stats(self, interaction : discord.Interaction, button : discord.ui.Button):
        stats_emb = discord.Embed(
            title = "<:VerifiedDev:905668791831265290> Miscellaneous Statistics :",
            colour = COLOUR)
        stats_emb.timestamp = discord.utils.utcnow()
        if interaction.user.is_on_mobile():
            stats_emb.description = f"\n Shows Code Related Things :\n" \
                                    f"```prolog\n - Total Classes    : {await misc('Source/', '.py', 'class'):,}" \
                                    f"\n - Total Functions  : {await misc('Source/', '.py', 'def'):,}" \
                                    f"\n - Total Lines      : {await tl('Source', '.py'):,}```"
            await interaction.response.send_message(embed = stats_emb, ephemeral = True)
        else:
            stats_emb.description = f"\n Shows Code Related Things :\n" \
                                    f"```ansi\n[0;1;35;40m - [0m [0;1;34mTotal Classes[0m   [0;1;35;40m : [0m [0;1;31m{await misc('Source/', '.py', 'class'):,}[0m" \
                                    f"\n[0;1;35;40m - [0m [0;1;34mTotal Functions[0m [0;1;35;40m : [0m [0;1;31m{await misc('Source/', '.py', 'def'):,}[0m" \
                                    f"\n[0;1;35;40m - [0m [0;1;34mTotal Lines[0m     [0;1;35;40m : [0m [0;1;31m{await tl('Source', '.py'):,}[0m```"
            await interaction.response.send_message(embed = stats_emb, ephemeral = True)
        
    # Shows System Usage at the current moment.
    @discord.ui.button(label = "System Info", style = discord.ButtonStyle.blurple, emoji = "<a:Info:905750331789561856>", custom_id = "Usage")
    async def sys_usage(self, interaction : discord.Interaction, button : discord.ui.Button):
        core_count = psutil.cpu_count()
        cpu_usage = psutil.cpu_percent()
        mem_per = psutil.virtual_memory().percent
        mem_gb = psutil.virtual_memory().available / 1024 ** 3
        ram_usage = psutil.Process().memory_full_info().uss / 1024 ** 2

        sys_usage_emb = discord.Embed(
            title = "<:WinCogs:898591890209910854> System Usage :",
            colour = COLOUR)
        sys_usage_emb.timestamp = discord.utils.utcnow()
        if interaction.user.is_on_mobile():
            sys_usage_emb.description = f"```prolog\n> CPU Usedm          : {cpu_usage:.2f} %\n" \
                                        f"> CPU Core Count    : {core_count} Cores\n" \
                                        f"> Memory Used       : {ram_usage:.2f} Megabytes\n" \
                                        f"> Memory Available  : {mem_gb:.3f} GB [ {mem_per} % ]\n```"
            await interaction.response.send_message(embed = sys_usage_emb, ephemeral = True)
        else:
            sys_usage_emb.description = f"```ansi\n[0;1;37;40m > [0m [0;1;34mCPU Used[0m          [0;1;35;40m : [0m [0;1;31m{cpu_usage:.2f} %[0m\n" \
                                        f"[0;1;37;40m > [0m [0;1;34mCPU Core Count[0m    [0;1;35;40m : [0m [0;1;31m{core_count} Cores[0m\n" \
                                        f"[0;1;37;40m > [0m [0;1;34mMemory Used[0m       [0;1;35;40m : [0m [0;1;31m{ram_usage:.2f} Megabytes[0m\n" \
                                        f"[0;1;37;40m > [0m [0;1;34mMemory Available[0m  [0;1;35;40m : [0m [0;1;31m{mem_gb:.3f} GB [ {mem_per} % ][0m\n```"
            await interaction.response.send_message(embed = sys_usage_emb, ephemeral = True)
    
    # Get latest Github commits
    @discord.ui.button(label = "Github Commits", style = discord.ButtonStyle.blurple, emoji = "<a:WumpusHypesquad:905661121501990923>", custom_id = "Commits")
    async def commits(self, interaction : discord.Interaction, button : discord.ui.Button):
        commit_emb = discord.Embed(
            title = "<:WinGIT:898591166864441345> My Latest Changes :",
            description = f"**[Github](<https://github.com/BSOD2528/Geralt>)** repository if you want to check things out <:verykewl:916903265541689445> \n\n>>> {Latest_Commit(MAX = 5)}",
            colour = COLOUR)
        commit_emb.timestamp = discord.utils.utcnow()
        commit_emb.set_footer(text = "If the link is throwing an error, it means commit has to be pushed.")
        await interaction.response.send_message(embed = commit_emb, ephemeral = True)

# Sub - Class for Confirmation based commands which utilises buttons.
class Confirmation(discord.ui.View):
    def __init__(self, ctx : GeraltContext, yes, no):
        super().__init__()
        self.ctx = ctx
        self.yes = yes
        self.no = no

    @discord.ui.button(label = "Yes", style = discord.ButtonStyle.blurple, emoji = "<:WinCheck:898572324490604605>")
    async def confirmed(self, interaction : discord.Interaction, button : discord.ui.Button):
        await self.yes(self, interaction, button)
    
    @discord.ui.button(label = "No", style = discord.ButtonStyle.danger, emoji = "<:WinUncheck:898572376147623956> ")
    async def cancelled(self, interaction : discord.Interaction, button : discord.ui.Button):
        await self.no(self, interaction, button)   
    
    async def interaction_check(self, interaction : discord.Interaction) -> bool:
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{self.ctx.clean_prefix}{self.ctx.command}` for the `{self.ctx.command}` command <:SarahPray:920484222421045258>"
        if interaction.user != self.ctx.author:
                return await interaction.response.send_message(content = f"{pain}", ephemeral = True)
        return True

#---#
  
#Sub - Classes for User PFP
class PFP(discord.ui.View):
    def __init__(self, bot, ctx : GeraltContext, user : discord.User):
        super().__init__(timeout = 60)
        self.ctx = ctx
        self.bot = bot
        self.user = user

    @discord.ui.button(label = "JPG", style = discord.ButtonStyle.gray, emoji = "<:ImageIcon:933966387477630996>")
    async def jpg(self, interaction : discord.Interaction, button : discord.ui.Button):
        user = self.user 
        button.disabled = True
        await interaction.message.edit(view = self)
        await interaction.response.send_message(f"Download it as a [**JPG**](<{user.display_avatar.with_static_format('jpg')}>)", ephemeral = True)
    
    @discord.ui.button(label = "PNG", style = discord.ButtonStyle.gray, emoji = "<:ImageIcon:933966387477630996>")
    async def png(self, interaction : discord.Interaction, button : discord.ui.Button):
        user = self.user
        button.disabled = True
        await interaction.message.edit(view = self)
        await interaction.response.send_message(f"Download it as a [**PNG**](<{user.display_avatar.with_static_format('png')}>)", ephemeral = True)
    
    @discord.ui.button(label = "WEBP", style = discord.ButtonStyle.gray, emoji = "<:ImageIcon:933966387477630996>")
    async def webp(self, interaction : discord.Interaction, button : discord.ui.Button):
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

    async def send(self, ctx : commands.Context):
        pfp_emb = discord.Embed(
            title = f"{str(self.user)}'s Avatar",
            url = self.user.display_avatar.url,
            colour = self.bot.colour)
        pfp_emb.set_image(url = self.user.display_avatar.with_static_format("png"))
        pfp_emb.timestamp = discord.utils.utcnow()
        self.message = await ctx.reply(embed = pfp_emb , view = self, mention_author = False)

# Views for leaving the guild
class Leave(discord.ui.View):
    def __init__(self, ctx : GeraltContext, guild : discord.Guild):
        super().__init__()
        self.ctx = ctx
        self.guild = guild
    
    @discord.ui.button(label = "Leave Guild", style = discord.ButtonStyle.grey, emoji = "<a:Byee:915568796536815616>")
    async def leave_guild(self, interaction : discord.Interaction, button : discord.ui.Button):
        await self.guild.leave()
        button.disabled = True
        await interaction.message.edit(view = self)
        await interaction.response.send_message(content = "Done <a:Comfort:918844984621428787>", ephemeral = True)
    
    @discord.ui.button(label = "Delete", style = discord.ButtonStyle.red, emoji = "<a:Trash:906004182463569961>")
    async def delete_message(self, interaction : discord.Interaction, button : discord.ui.Button):
        await interaction.message.delete()

    async def interaction_check(self, interaction : discord.Interaction) -> bool:
        pain = f"This view can't be handled by you at the moment <:SarahPray:920484222421045258>"
        if interaction.user == self.ctx.author:
            return True
        await interaction.response.send_message(content = f"{pain}", ephemeral = True)  