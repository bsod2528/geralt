import io
import typing
import pygit2
import psutil
import dotenv
import random
import discord
import aiohttp
import datetime
import itertools
import traceback
import asyncpg as PSQL

from discord.ext import commands
from dotenv import dotenv_values

from Source.Kernel.Utilities.Crucial import total_lines as tl, misc
import Source.Kernel.Views.Paginator as Paginator

dotenv.load_dotenv()

CONFIG  =   dotenv_values("config.env")
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
    @discord.ui.button(label = "Misc.", style = discord.ButtonStyle.blurple, emoji = "<a:WumpusVibe:905457020575031358>", custom_id = "Stats")
    async def stats(self, interaction : discord.Interaction, button : discord.ui.Button):
        stats_emb = discord.Embed(
            title = "<:VerifiedDev:905668791831265290> Miscellaneous Statistics :",
            description = f"\n Shows Code Related Things :\n" \
                          f"```ansi\n[0;1;35;40m - [0m [0;1;34mTotal Classes[0m   [0;1;35;40m : [0m [0;1;31m{await misc('Source/', '.py', 'class'):,}[0m" \
                          f"\n[0;1;35;40m - [0m [0;1;34mTotal Functions[0m [0;1;35;40m : [0m [0;1;31m{await misc('Source/', '.py', 'def'):,}[0m"
                          f"\n[0;1;35;40m - [0m [0;1;34mTotal Lines[0m     [0;1;35;40m : [0m [0;1;31m{await tl('Source', '.py'):,}[0m```",
            colour = COLOUR)
        stats_emb.timestamp = discord.utils.utcnow()
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
            description = f"```ansi\n[0;1;37;40m > [0m [0;1;34mCPU Used[0m          [0;1;35;40m : [0m [0;1;31m{cpu_usage:.2f} %[0m\n" \
                          f"[0;1;37;40m > [0m [0;1;34mCPU Core Count[0m    [0;1;35;40m : [0m [0;1;31m{core_count} Cores[0m\n" \
                          f"[0;1;37;40m > [0m [0;1;34mMemory Used[0m       [0;1;35;40m : [0m [0;1;31m{ram_usage:.2f} Megabytes[0m\n" \
                          f"[0;1;37;40m > [0m [0;1;34mMemory Available[0m  [0;1;35;40m : [0m [0;1;31m{mem_gb:.3f} GB [ {mem_per} % ][0m\n```",
            colour = COLOUR)
        sys_usage_emb.timestamp = discord.utils.utcnow()
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

#---#

# Sub - Class for Confirmation based commands which utilises buttons.
class Confirmation(discord.ui.View):
    def __init__(self, ctx, yes, no):
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

#---#
  
#Sub - Classes for User PFP
class PFP(discord.ui.View):
    def __init__(self, bot, ctx : commands.context, user : discord.User):
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

    async def send(self, ctx : commands.context):
        pfp_emb = discord.Embed(
            title = f"{str(self.user)}'s Avatar",
            url = self.user.display_avatar.url,
            colour = self.bot.colour)
        pfp_emb.set_image(url = self.user.display_avatar.with_static_format("png"))
        pfp_emb.timestamp = discord.utils.utcnow()
        self.message = await ctx.reply(embed = pfp_emb , view = self, mention_author = False)

#---#

# Error - Handler View
class Traceback(discord.ui.View):
    def __init__(self, bot, ctx, error):
        super().__init__(timeout = 60)
        self.bot = bot
        self.ctx = ctx
        self.error = error

    @discord.ui.button(label = "Traceback", style = discord.ButtonStyle.blurple, emoji = "<:WinTerminal:898609124982554635>")
    async def traceback(self, interaction : discord.Interaction, button : discord.ui.Button):
        button.disabled = True
        button.style = discord.ButtonStyle.green
        error = getattr(self.error, "original", self.error)
        error_emb = discord.Embed(
            title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {self.ctx.command}",
            description = f"```yaml\n Quick Tip : Read the last 2 - 3 lines for proper info.\n```\n```py\n {''.join(traceback.format_exception(type(error), error, error.__traceback__))}\n```\n",   
            colour = 0x2F3136)
        await interaction.message.edit(view = self)
        await interaction.response.send_message(embed = error_emb, ephemeral = True)    
    
    @discord.ui.button(label = "Command Help", style = discord.ButtonStyle.blurple, emoji = "<a:Trash:906004182463569961>")
    async def cmd_help(self, interaction : discord.Interaction, button : discord.ui.Button):
        button.disabled = True
        button.style = discord.ButtonStyle.green
        command_help = discord.Embed(
            title = f"<:GeraltRightArrow:904740634982760459> Command Help : {self.ctx.command}",
            description = f"> {self.ctx.command.help}",
            colour = 0x2F3136)
        command_help.timestamp = discord.utils.utcnow()
        command_help.set_footer(text = f"Invoked by {interaction.user}", icon_url = interaction.user.display_avatar.url)
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

#---#

# Error - Handler View for commands.BadArgumemt
class CommandSyntax(discord.ui.View):
    def __init__(self, bot, ctx, error):
        super().__init__(timeout = 60)
        self.bot = bot
        self.ctx = ctx
        self.error = error

    @discord.ui.button(label = "Syntax", style = discord.ButtonStyle.blurple, emoji = "<a:CoffeeSip:907110027951742996>")
    async def cmd_syntax(self, interaction : discord.Interaction, button : discord.ui.Button):
        button.disabled = True
        button.style = discord.ButtonStyle.green
        try:
            command_name = f"{self.ctx.clean_prefix}{self.ctx.command} {self.ctx.command.signature}"
            syntax_emb = discord.Embed(
                title = f"<:GeraltRightArrow:904740634982760459> COMMAND SYNTAX : {self.ctx.clean_prefix}{self.ctx.command}",
                description = f"\n```prolog\n{command_name}" \
                          f"\n{' ' * (len([item[::-1] for item in command_name[::-1].split(self.error.param.name[::-1], 1)][::-1][0]) - 1)}{'-' * (len(self.error.param.name) + 2)}" \
                          f"\n\"{self.error.param.name}\" is a required argument which you have not passed\n```",
                colour = 0x2F3136)
            syntax_emb.timestamp = discord.utils.utcnow()
            syntax_emb.set_footer(text = f"Run {self.ctx.clean_prefix}{self.ctx.command} help for more help")
            await interaction.message.edit(view = self)
            await interaction.response.send_message(embed = syntax_emb, ephemeral = True)
        except:
            await interaction.response.send_message(content = f"This was meant for a command error\n> This is a hierarchy issue.\n", ephemeral = True)    

    @discord.ui.button(label = "Command Help", style = discord.ButtonStyle.blurple, emoji = "<a:Trash:906004182463569961>")
    async def cmd_help(self, interaction : discord.Interaction, button : discord.ui.Button):
        button.disabled = True
        button.style = discord.ButtonStyle.green
        command_help = discord.Embed(
            title = f"<:GeraltRightArrow:904740634982760459> Command Help : {self.ctx.command}",
            description = f"> {self.ctx.command.help}",
            colour = 0x2F3136)
        command_help.timestamp = discord.utils.utcnow()
        command_help.set_footer(text = f"Invoked by {interaction.user}", icon_url = interaction.user.display_avatar.url)
        await interaction.message.edit(view = self)
        try:
            await interaction.response.send_message(embed = command_help, ephemeral = True)
        except Exception as exception:
            await interaction.response.send_message(content = exception, ephemeral = True)    

    @discord.ui.button(label = "Traceback", style = discord.ButtonStyle.blurple, emoji = "<:WinTerminal:898609124982554635>")
    async def traceback(self, interaction : discord.Interaction, button : discord.ui.Button):
        button.disabled = True
        button.style = discord.ButtonStyle.green
        error = getattr(self.error, "original", self.error)
        error_emb = discord.Embed(
            title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {self.ctx.command}",
            description = f"```yaml\n Quick Tip : Read the last 2 - 3 lines for proper info.\n```\n```py\n {''.join(traceback.format_exception(type(error), error, error.__traceback__))}\n```\n",   
            colour = 0x2F3136)
        await interaction.message.edit(view = self)
        try:
            await interaction.response.send_message(embed = error_emb, ephemeral = True)    
        except Exception as exception:
            await interaction.response.send_message(content = exception, ephemeral = True)    
    
    async def send(self, ctx):
        common_error = discord.Embed(
                title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {ctx.command}",
                description = f"```py\n{self.error}\n```\nClick on the `Syntax` Button for the proper syntax of `{self.ctx.command}`",
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

#---#

# Nitro Command View
class Nitro(discord.ui.View):
    def __init__(self, user : discord.Member = None):
        super().__init__()

    @discord.ui.button(label = "Avail Nitro", style = discord.ButtonStyle.green, emoji = "<a:WumpusHypesquad:905661121501990923>")
    async def nitro(self, interaction : discord.Interaction, button : discord.ui.Button):
        button.disabled = True
        button.label = "Claimed"
        await interaction.message.edit(view = self)
        await interaction.user.send(content = f"discord.gift/R1cKr0OlL3d")
        await interaction.response.send_message(content = "https://imgur.com/NQinKJB", ephemeral = True)     

#---#

# Classes for Pop Game
class PopButton(discord.ui.Button):
    async def callback(self, interaction : discord.Interaction):
        await interaction.response.defer()
        self.disabled = True
        self.style = discord.ButtonStyle.grey
        await self.view.message.edit(view = self.view)
    
class Pop(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout = 90)
        self.ctx = ctx
        self.message : typing.Optional[discord.Message] = None
    
    async def start(self):
        for button in range(5):
            self.add_item(PopButton(label = "\u200b", style = discord.ButtonStyle.blurple))
        self.message = await self.ctx.send("\u200b", view = self)
    
    async def on_timeout(self) -> None:
        for view in self.children:
            view.disabled = True
            view.style = discord.ButtonStyle.grey
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
            self.add_item(PopButton(label = "\u200b", style = discord.ButtonStyle.blurple))
        self.message = await self.ctx.send("\u200b", view = self)
    
    async def on_timeout(self) -> None:
        for view in self.children:
            view.disabled = True
            view.style = discord.ButtonStyle.grey
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
            self.add_item(PopButton(label = "\u200b", style = discord.ButtonStyle.blurple))
        self.message = await self.ctx.send("\u200b", view = self)
    
    async def on_timeout(self) -> None:
        for view in self.children:
            view.disabled = True
            view.style = discord.ButtonStyle.grey
            await self.message.edit(view = self)
    
    async def interaction_check(self, interaction : discord.Interaction) -> bool:
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{self.ctx.clean_prefix}{self.ctx.command}` for the `{self.ctx.command}` command <:SarahPray:920484222421045258>"
        if interaction.user == self.ctx.author:
            return True
        await interaction.response.send_message(content = f"{pain}", ephemeral = True)  

#---#

# Simple Click Game - Idea by InterStella0 [ Github ID ]
class ClickSize(commands.FlagConverter, prefix = "--", delimiter = " ", case_insensitive = True):
    size : typing.Optional[int]

emoji_list = ["<a:Click:973748305416835102>", "<:Bonked:934033408106057738>", "<a:RooSitComfortPatAnotherRoo:916125535015419954>", "<a:IPat:933295620834336819>", "<:DuckSip:917006564265705482>", "<a:SpongebobVibe:913798501123645480>", "<a:ZizzyHappy:915131835443474492>", "<a:ReiPet:965800035054931998>"]

class ClickButton(discord.ui.Button):
    def __init__(self, bot, ctx):
        super().__init__(
            label = "Click",
            style = discord.ButtonStyle.grey,
            emoji = random.choice(emoji_list))
        self.bot = bot
        self.ctx = ctx
    
    async def callback(self, interaction : discord.Interaction):
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{self.ctx.clean_prefix}{self.ctx.command}` for the `{self.ctx.command}` command <:SarahPray:920484222421045258>"
        if interaction.user == self.ctx.author:
            try:
                await interaction.response.defer()
                guild_score_query = "INSERT INTO click_guild (guild_id, player_id, clicks, player_name)" \
                        "VALUES ($1, $2, 1, $3)" \
                        "ON CONFLICT(guild_id, player_id)" \
                        "DO UPDATE SET clicks = click_guild.clicks + 1, player_name = $3" 
                await self.bot.db.execute(guild_score_query, interaction.guild_id, interaction.user.id, str(self.ctx.author))
                global_score_query = "INSERT INTO click_global (player_id, clicks, player_name, player_pfp)" \
                        "VALUES ($1, 1, $2, $3)" \
                        "ON CONFLICT(player_id)" \
                        "DO UPDATE SET clicks = click_global.clicks + 1, player_name = $2, player_pfp = $3"
                await self.bot.db.execute(global_score_query, interaction.user.id, str(self.ctx.author), str(self.ctx.author.display_avatar))
            except Exception as exception:
                await interaction.followup.send(content = f"```py\n{exception}\n```", ephemeral = True)
        else:
            await interaction.response.send_message(content = f"{pain}", ephemeral = True)  

class ClickGame(discord.ui.View):
    def __init__(self, bot, ctx, *, size : typing.Optional[int]):
        super().__init__(timeout = 60)
        self.bot = bot
        self.ctx = ctx
        self.size = size

        for button in range(self.size):
            if self.size > 10:
                raise commands.BadArgument("Size should be less than \"10\"")
            if not self.size:
                self.add_item(ClickButton(self.bot, self.ctx))
            else:
                self.add_item(ClickButton(self.bot, self.ctx))
    
    @discord.ui.button(label = "Scores", style = discord.ButtonStyle.grey, emoji = "\U00002728", row = 2)
    async def on_click_guild_leaderboard(self, interaction : discord.Interaction, button : discord.ui.Button):
        try:
            guild_score_query = await self.bot.db.fetchval("SELECT (clicks) FROM click_guild WHERE guild_id = $1 AND player_id = $2", interaction.guild_id, self.ctx.author.id)
            await interaction.response.defer()
            if not guild_score_query:
                await interaction.followup.send(content = f"{self.ctx.author.mention} has yet to click on the button in **{interaction.guild.name}** <:TokoOkay:898611996163985410>", ephemeral = True)
            else:
                await interaction.followup.send(content = f"{self.ctx.author.mention} has clicked a total of `{guild_score_query}` times in **{interaction.guild.name}** <:TokoOkay:898611996163985410>", ephemeral = True)
        except Exception as exception:
            await interaction.followup.send(content = f"```py\n{exception}\n```", ephemeral = True)

    @discord.ui.button(label = "Help", style = discord.ButtonStyle.green, emoji = "<:DuckThumbsUp:917007413259956254>", row = 2)
    async def on_click_help(self, interaction : discord.Interaction, button : discord.ui.Button):
        await interaction.response.defer()
        help_content = f"{interaction.user.mention}\n\n────\n> │ ` ─ ` Click on the \"Click\" button to attain points. You have a 60 second time limit. Try to score much as possible.\n> │ ` ─ ` Go up the leaderboard by playing en number of times. Enjoy!\n────\nhttps://imgur.com/a/S0LyjuB"
        await interaction.followup.send(content = help_content, ephemeral = True)

    async def send(self, ctx):
        self.message = await ctx.reply(content = "Click as fast as you can and earn points <a:CrazyRolex:966181282914660402>", view = self)
        return self.message

    async def on_timeout(self) -> None:
        for view in self.children:
            view.disabled = True
        return await self.message.edit(content = f"**{self.ctx.author}** - you've been timed out due to inactivity. To start clicking again, rerun `{self.ctx.clean_prefix}{self.ctx.command}` and be the number one on the leaderboard <a:Comfort:918844984621428787>", view = self)

class ClickLeaderboard(discord.ui.View):
    def __init__(self, bot, ctx):
        super().__init__(timeout = 60)
        self.bot = bot
        self.ctx = ctx

    @discord.ui.button(label = "Global Leaderboard", style = discord.ButtonStyle.blurple, emoji = "<a:RooSitComfortPatAnotherRoo:916125535015419954>")
    async def click_global_leaderboard(self, interaction : discord.Interaction, button : discord.ui.Button):
        try:
            await interaction.response.defer()
            global_leaderboard_query = await self.bot.db.fetch("SELECT player_name, clicks, player_pfp FROM click_global ORDER BY clicks DESC LIMIT 10")
            serial_no = 1
            leaderboard = []
            for data in global_leaderboard_query:
                leaderboard.append(f"> **{serial_no})** [**{data['player_name']}**]({data['player_pfp']}) \u200b : `{data['clicks']}`\n")
                serial_no += 1

            while leaderboard:  
                global_leaderboard_emb = discord.Embed(
                    description = f"The following showcases the top 10 scores for `{self.ctx.clean_prefix}click`",
                    colour = self.bot.colour)
                global_leaderboard_emb.add_field(
                    name = "Top 10 Global Scores",
                    value = f"".join(leaderboard[:10]))
                global_leaderboard_emb.timestamp = discord.utils.utcnow()
                global_leaderboard_emb.set_thumbnail(url = "https://discords.com/_next/image?url=https%3A%2F%2Fcdn.discordapp.com%2Femojis%2F929249429486178334.gif%3Fv%3D1&w=64&q=75")
                global_leaderboard_emb.set_author(name = "Global Click Scores")
                global_leaderboard_emb.set_footer(text = f"Run {self.ctx.clean_prefix}click for more sub ─ commands.")
                leaderboard = leaderboard[10:]
            await interaction.followup.send(embed = global_leaderboard_emb, ephemeral = True)
        except Exception as exception:
            await interaction.response.send_message(content = f"```py\n{exception}\n```", ephemeral = True)

    async def send(self):
        guild_score_query = await self.bot.db.fetch("SELECT player_id, clicks FROM click_guild WHERE guild_id = $1 ORDER BY clicks DESC LIMIT 10", self.ctx.guild.id)
        serial_no = 1
        leaderboard = []
        for data in guild_score_query:
            leaderboard.append(f"> **{serial_no}).** <@{data['player_id']}> : `{data['clicks']}`\n")
            serial_no += 1
        
        if not guild_score_query:
            return await self.ctx.reply(f"No one from **{self.ctx.guild}** has played `{self.ctx.clean_prefix}click` game <a:Noo:915422306896072744>. Feel honoured and be the first one !")
        else:
            while leaderboard:
                leaderboard_emb = discord.Embed(
                    title = f"Click Scores for {self.ctx.guild} :",
                    description = f"The following showcases the top 10 scores for `{self.ctx.clean_prefix}click`",
                    colour = self.bot.colour)
                leaderboard_emb.add_field(
                    name = "Top 10 Scores",
                    value = "".join(leaderboard[:10]))
                leaderboard_emb.timestamp = discord.utils.utcnow()
                leaderboard_emb.set_thumbnail(url = self.ctx.guild.icon.url)
                leaderboard_emb.set_footer(text = f"Run {self.ctx.clean_prefix}help click for more sub ─ commands.")
                leaderboard = leaderboard[10:]
        self.message = await self.ctx.reply(embed = leaderboard_emb, view = self)
        return self.message

    async def on_timeout(self) -> None:
        for view in self.children:
            view.disabled = True
            return await self.message.edit(view = self)

#---#

# Views for Tags
class TagButton(discord.ui.View):
    def __init__(self, bot, ctx):
        super().__init__(timeout = 100)
        self.bot = bot
        self.ctx = ctx

    class ModalTag(discord.ui.Modal, title = "Create a Tag !"):
        def __init__(self, bot, ctx):
            super().__init__()
            self.bot = bot
            self.ctx = ctx

        tag_name = discord.ui.TextInput(
            label = "Name",
            placeholder = "Please enter the name of the tag.")
    
        tag_content = discord.ui.TextInput(
            label = "Content",
            style = discord.TextStyle.paragraph,
            required = True, 
            placeholder = "Enter the content of the tag.")
    
        async def on_submit(self, interaction : discord.Interaction) -> None:
            try:
                blacklisted_words = ["make", "raw", "info", "transfer", "delete", "edit", "list", "all"]
                if self.tag_name.value.strip() in blacklisted_words:
                    return await interaction.response.send_message(content = f"{interaction.user.mention} ─ `make` is a reserved keyword. Please try again using another word", ephemeral = True)
                else:
                    await self.bot.db.execute(f"INSERT INTO tags (name, content, author_id, author_name, guild_id, created_on, jump_url) VALUES ($1, $2, $3, $4, $5, $6, $7)", self.tag_name.value.strip(), self.tag_content.value, self.ctx.author.id, str(self.ctx.author), self.ctx.guild.id, self.ctx.message.created_at, self.ctx.message.jump_url)
                    id = await self.bot.db.fetchval("SELECT id FROM tags WHERE name = $1 AND content = $2", self.tag_name.value, self.tag_content.value)
                    
                    class TagContent(discord.ui.View):
                        def __init__(self, bot, ctx):
                            super().__init__()
                            self.bot = bot
                            self.ctx = ctx

                        @discord.ui.button(label = "Content", style = discord.ButtonStyle.grey, emoji = "<:NanoTick:925271358735257651>")
                        async def on_tag_make_content_view(self, interaction : discord.Interaction, button : discord.ui.Button):
                            try:
                                content = await self.bot.db.fetchval("SELECT content FROM tags WHERE guild_id = $1 AND id = $2 AND author_id = $3", self.ctx.guild.id, id, self.ctx.author.id)
                                await interaction.response.send_message(content = f"\"{content}\"", ephemeral = True)
                            except Exception as exception:
                                await interaction.response.send_message(content = f"```py\n{exception}\n```", ephemeral = True)

                    await interaction.response.send_message(content = f"`{self.tag_name.value}` ─ tag has been created by {interaction.user.mention}. The following points showcase the entire details of the tag :\n\n>>> ────\n` ─ ` Name : \"{self.tag_name.value}\" ─ (`{id}`)\n` ─ ` Created On : {self.bot.datetime(interaction.created_at, style = 'f')}\n────", ephemeral = False, view = TagContent(self.bot, self.ctx))
            
            except PSQL.UniqueViolationError:
                return await interaction.response.send_message(content = f"`{self.tag_name.value}` ─ is a tag which is already present. Please try again with another with another name", ephemeral = True)
            except Exception as exception:
                return await interaction.response.send_message(content = f"```py\n{exception}\n```", ephemeral = True)
        
        async def on_error(self, interaction : discord.Interaction, error : Exception) -> None:
            async with aiohttp.ClientSession() as session:
                modal_webhook = discord.Webhook.partial(id = CONFIG.get("ERROR_ID"), token = CONFIG.get("ERROR_TOKEN"), session = session)
                data = "".join(traceback.format_exception(type(error), error, error.__traceback__))
                try:
                    await modal_webhook.send(content = f"```py\n{data}\n```\n|| Break Point ||")
                except(discord.HTTPException, discord.Forbidden):
                    await modal_webhook.send(file = discord.File(io.StringIO(data), filename = "Traceback.py"))
                    await modal_webhook.send(content = "|| Break Point ||")
                await session.close()

    @discord.ui.button(label = "Create Tag", style = discord.ButtonStyle.grey, emoji = "<a:PandaNote:961260552435413052>")
    async def create_tag(self, interaction : discord.Interaction, button : discord.ui.Button):
        pain = f"{interaction.user.mention} ─ This view can't be handled by you at the moment <:Bonked:934033408106057738>, it is meant for {self.ctx.author.mention}\nInvoke for youself by running `{self.ctx.clean_prefix}{self.ctx.command}` for the `{self.ctx.command}` command <:SarahPray:920484222421045258>"
        if interaction.user == self.ctx.author:
            button.disabled = True
            await interaction.message.edit(view = self)
            await interaction.response.send_modal(self.ModalTag(self.bot, self.ctx))
        else:
            await interaction.response.send_message(content = f"{pain}", ephemeral = True)        
        
    @discord.ui.button(label = "Help", style = discord.ButtonStyle.grey, emoji = "<a:ReiPet:965800035054931998>")
    async def command_help(self, interaction : discord.Interaction, button : discord.ui.Button):
        
        class TagMakeArgHelpButton(discord.ui.View):
            
            @discord.ui.button(label = "Arguments Taken", style = discord.ButtonStyle.green, emoji = "<a:PandaHappy:915131837158936596>")
            async def arg_button(self, interaction : discord.Interaction, button : discord.ui.button):
                await interaction.response.send_message(content = f"{interaction.user.mention}\n\n>>> ────\n<:GeraltRightArrow:904740634982760459> The following list shows what arguments can be inputted inside the tag :\n │ ` ─ ` Text : Just regular test lol <a:RooSitComfortPatAnotherRoo:916125535015419954>\n │ ` ─ ` Emotes : Emote IDs have to be sent for **custom emotes**. [**Click here to know how to get the custom emote ID**](<https://docs.parent.gg/how-to-obtain-emoji-ids/>). For **default emotes** just do `:<emote>:`\n │ ` ─ ` Codeblocks : A code snippet can be sent by using \`\`\`<language>new line<code>\`\`\` \n │ ` ─ ` Multimedia [ Image & Videos ] : Files which have been sent in discord can be used. Ensure to right click on `video/image` and copy the **link** and paste it.\n────", ephemeral = True)

        await interaction.response.send_message(content = f"{interaction.user.mention}\n\n────\n**Click on the `Arguments Taken` Button for a list of arguments allowed.**\n\nA modal will pop open for you. The following points give a small gist :\n> │ ` ─ ` \"Name\" : Where you're supposed to enter the name of the tag you would like to create.\n> │ ` ─ ` \"Content\" : Where you enter the content for that tag which will be sent upon invoked.\n────\nhttps://i.imgur.com/yAp0dWy.gif", ephemeral = True, view = TagMakeArgHelpButton())

    @discord.ui.button(label = "Exit", style = discord.ButtonStyle.red, emoji = "<a:Byee:915568796536815616>")
    async def exit_tag_creation(self, interaction : discord.Interaction, button : discord.ui.Button):
        pain = f"{interaction.user.mention} ─ This view can't be handled by you at the moment <:Bonked:934033408106057738>, it is meant for {self.ctx.author.mention}\nInvoke for youself by running `{self.ctx.clean_prefix}{self.ctx.command}` for the `{self.ctx.command}` command <:SarahPray:920484222421045258>"
        if interaction.user == self.ctx.author:
            await interaction.response.defer()
            await interaction.delete_original_message()
        else:
            await interaction.response.send_message(content = f"{pain}", ephemeral = True)        

    async def send(self, ctx):
        self.message = await ctx.send(content = f"**{ctx.author}** ─ please utilise the button below to create a new `tag` <a:IWait:948253556190904371>", view = self)
        return self.message
        
    async def on_timeout(self) -> None:
        try:
            for view in self.children:
                view.label = "Timed out"
                view.emoji = "<:NanoCross:965845144307912754>"
                view.disabled = True
            return await self.message.edit(content = f"**{self.ctx.author}** ─ I'm sorry to say that this view has timed out <a:VariableCry:942041851228196884>. Please run `{self.ctx.clean_prefix}tag make` to make a tag <a:ZizzyHappy:915131835443474492>", view = self)        
        except Exception:
            pass
