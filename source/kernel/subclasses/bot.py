import io
import os
import sys
import time
import dotenv
import typing
import discord
import asyncpg
import aiohttp
import humanize
import traceback
import colorama as colour

from dotenv import dotenv_values
from discord import app_commands
from discord.ext import commands

from .embed import BaseEmbed
from ..views.meta import Info
from .context import GeraltContext

COGS_EXTENSIONS : typing.List = [    
    "jishaku",
    "source.cogs.fun",
    "source.cogs.tags",
    "source.cogs.meta",
    "source.cogs.help",
    "source.cogs.guild",
    "source.cogs.events",
    "source.cogs.utility",
    "source.cogs.developer",
    "source.cogs.moderation",
    "source.cogs.errorhandler"
]

dotenv.load_dotenv()
os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True" 

CONFIG = dotenv_values("config.env")
TOKEN = CONFIG.get("TOKEN")
DB_URL = CONFIG.get("DB_URL")

                #BSOD#0067 [ME]      SID#1380 [Zeus432]
DEVELOPER_IDS = [750979369001811982]#, 760823877034573864]

colour.init()

async def db_connect(): 
    try:
        print(f"{colour.Fore.LIGHTYELLOW_EX}-> {time.strftime('%c', time.localtime())} ─ Waking up {colour.Style.RESET_ALL}")
        print(f"{colour.Fore.BLUE}-> {time.strftime('%c', time.localtime())} ─ Establishing connection with my database. {colour.Style.RESET_ALL}")
        Geralt.db = await asyncpg.create_pool(dsn = DB_URL)
        print(f"{colour.Fore.GREEN}-> {time.strftime('%c', time.localtime())} ─ Connection established successfully. {colour.Style.RESET_ALL}")
    except Exception as exception:
        print(f"{colour.Fore.RED}-> {time.strftime('%c', time.localtime())} ─ Couldnt connect due to : {exception} {colour.Style.RESET_ALL}")

class Geralt(commands.Bot): 
    """Geralt's subclass of :class: `commands.Bot`."""
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            status = discord.Status.online,
            intents = discord.Intents.all(),
            tree_cls = app_commands.CommandTree,
            activity = discord.Activity(type = discord.ActivityType.playing, name = "Waking up to Die"),
            command_prefix = self.get_prefix,
            case_insensitive = True,
            strip_after_prefix = True)

        self.colour = discord.Colour.from_rgb(117, 128, 219)
        self.mentions = discord.AllowedMentions.none()
        self.no_prefix : bool = False
        self.timestamp = discord.utils.format_dt        
        self.owner_ids : typing.List = DEVELOPER_IDS
        self.developer_mode : bool = False
        self.default_prefix = ".g"
        self.add_persistent_views = False
        
        # Geralt's Cache
        self.afk : typing.Dict = {}
        self.prefixes : typing.Dict = {} 
        self.blacklist : typing.Dict = set()
        self.ticket_init : typing.Dict = {}
        self.ticket_panel : typing.Dict = {}
        self.ticket_kernel : typing.Dict = {}
        self.ticket_message : typing.Dict = {}

    async def get_context(self, message : discord.Message, *, cls = GeraltContext) -> GeraltContext:
        return await super().get_context(message, cls = cls)

    async def on_error(self, event_method : str, *args : typing.Any, **kwargs : typing.Any) -> None:
        traceback_string = "".join(traceback.format_exception(*(einfo := sys.exc_info())))
        async with aiohttp.ClientSession() as session:  
            webhook = discord.Webhook.partial(id = CONFIG.get("ERROR_ID"), token = CONFIG.get("ERROR_TOKEN"), session = session)
            await webhook.send(f"An error occurred in an `{event_method}` event", file = discord.File(io.BytesIO(traceback_string.encode()), filename = "traceback.py"))
            await webhook.send("|| Break Point ||")
        await session.close()

    async def add_to_blacklist(self, user : discord.User, reason : str, url : str):
        query = "INSERT INTO blacklist VALUES ($1, $2, $3, $4)"
        if user.id in self.owner_ids:
            raise commands.BadArgument("They are one of the owners \U0001f480")
        else:
            await self.db.execute(query, user.id, reason, discord.utils.utcnow(), url)
            self.blacklist.add(user.id)
    
    async def remove_from_blacklist(self, user : discord.User):
        query = "DELETE FROM blacklist WHERE user_id = $1"
        await self.db.execute(query, user.id)
        self.blacklist.remove(user.id)

    async def get_prefix(self, message : discord.Message):
        guild_id = getattr(message.guild, "id", message.author.id)
        if (prefix := self.prefixes.get(guild_id)) is None:
            data = await self.db.fetchrow("SELECT guild_prefix FROM custom_prefix WHERE guild_id = $1", guild_id)
            prefix = self.default_prefix if data is None else data["guild_prefix"]
        if self.no_prefix is True and message.author.id in self.owner_ids:
            return [prefix, self.user.mention, ""]
        return [prefix, self.user.mention, self.default_prefix]

    async def setup_hook(self) -> None:
        print(f"{colour.Fore.BLUE}-> {time.strftime('%c', time.localtime())} ─ Loading all Extensions.{colour.Style.RESET_ALL}")
        self.tree.copy_global_to(guild = discord.Object(id = CONFIG.get("BSODsThings")))
        for extensions in COGS_EXTENSIONS:
            try:
                await self.load_extension(extensions)
            except Exception as exception:
                print(f"{colour.Fore.LIGHTRED_EX}-> {time.strftime('%c', time.localtime())} ─ {exception} : {exception} {colour.Style.RESET_ALL}\n")
        
        print(f"{colour.Fore.GREEN}-> {time.strftime('%c', time.localtime())} ─ Extensions Successfully Loaded. {colour.Style.RESET_ALL}")

        if not hasattr(self, "uptime"):
            self.uptime = discord.utils.utcnow()

    async def on_ready(self):
        afk_deets = await self.db.fetch("SELECT * FROM afk")
        prefix_deets = await self.db.fetch("SELECT * FROM custom_prefix")
        ticket_deets = await self.db.fetch("SELECT * FROM ticket_init")

        self.afk = {data["user_id"] : data["reason"] for data in afk_deets}
        self.tickets = {data["guild_id"] : data["sent_message_id"] for data in ticket_deets}
        self.prefixes = {data["guild_id"] : data["guild_prefix"] for data in prefix_deets}
        
        if not self.add_persistent_views:
            self.add_view(Info(self, GeraltContext))
            self.add_persistent_views = True

        fetch_blacklisted_members = await self.db.fetch("SELECT user_id FROM blacklist")
        self.blacklist.add(f"{users}" for users in fetch_blacklisted_members)        

        async with aiohttp.ClientSession() as session:  
            wbhk = discord.Webhook.partial(id = CONFIG.get("NOTIF_ID"), token = CONFIG.get("NOTIF_TOKEN"), session = session)
            await self.change_presence(
                status = discord.Status.idle,
                activity = discord.Activity(type = discord.ActivityType.listening, name = f".ghelp")) 
            #await wbhk.send(f"|| Break Point ||\n───\n<:GeraltRightArrow:904740634982760459> Came alive at ─ {self.timestamp(discord.utils.utcnow(), style = 'F')} Hi <a:Waves:920726389869641748>\n```prolog\n" \
                            #f"No. of Users ─ {len(list(self.get_all_members()))}\nNo. of Guilds ─ {len(self.guilds)}\nWoke up at ─ {time.strftime('%c', time.gmtime())}```")
            print(f"{colour.Fore.GREEN}-> {time.strftime('%c', time.localtime())} ─ Awakened {colour.Style.RESET_ALL}")
            await session.close()

    async def on_message(self, message : discord.Message):
        await self.wait_until_ready()
        afk_deets = await self.db.fetch("SELECT * FROM afk")
        
        if message.author.id in self.blacklist:
            return 

        if self.developer_mode is True:
            if message.author.id in self.owner_ids:
                await self.change_presence(status = discord.Status.invisible)
                return await self.process_commands(message)
            return
        
        if message.author.id in self.afk:
            for user in afk_deets:
                time = user["time"]
            current_time = discord.utils.utcnow() - time
            await message.reply(f"Welcome back <a:Waves:920726389869641748>. You were afk for : \"**{humanize.naturaldelta(current_time)}**\"", allowed_mentions = self.mentions)
            await self.db.execute("DELETE FROM afk WHERE user_id = $1", message.author.id)
            self.afk.pop(message.author.id)
        
        for pinged_user in message.mentions:
            if pinged_user.id in self.afk:
                for data in afk_deets:
                    time = data["time"]
                    reason = data["reason"]
                    current_time = discord.utils.utcnow() - time
                await message.reply(f"<:Join:932976724235395072> **{pinged_user}** has been afk :\n>>> <:ReplyContinued:930634770004725821>` ─ ` for : {reason}\n<:Reply:930634822865547294>` ─ ` since : {humanize.naturaldelta(current_time)}")

        if message.content in [self.user.mention]:
            current_prefix = await self.db.fetchval("SELECT (guild_prefix) FROM custom_prefix WHERE guild_id = $1", message.guild.id)
            if not current_prefix:
                current_prefix = self.default_prefix
            prefix_emb = BaseEmbed(
                description = f"`{current_prefix}`\n`.g`\n{self.user.mention}",
                colour = self.colour)
            prefix_emb.set_footer(text = f"Run {current_prefix}help prefix.")
            if message.guild.icon.url:
                prefix_emb.set_author(name = message.guild, icon_url = message.guild.icon.url)
            else:
                prefix_emb.set_author(name = message.guild)
            await message.reply(embed = prefix_emb, mention_author = False)
            
        await self.process_commands(message)   
    
Geralt = Geralt()

async def run():
    async with Geralt:
        Geralt.loop.create_task(db_connect())
        await Geralt.start(TOKEN)