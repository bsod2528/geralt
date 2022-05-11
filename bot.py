import os
import time
import dotenv
import typing
import discord
import asyncpg
import aiohttp  
import asyncio
import datetime
import colorama as colour

from dotenv import dotenv_values
from discord.ext import commands    


import Source.Kernel.Views.Interface as Interface 

COGS_EXTENSIONS    =   [    
    "jishaku",
    "Source.Cogs.Fun",
    "Source.Cogs.Tags",
    "Source.Cogs.Help",
    "Source.Cogs.Misc",
    "Source.Cogs.Guild",
    "Source.Cogs.Events",
    "Source.Cogs.Utility",
    "Source.Cogs.Developer",
    "Source.Cogs.Moderation",
    "Source.Cogs.ErrorHandler"
]
                    # BSOD#2528 [ ME ]  # SID#0007
DEVELOPER_IDS   =   [750979369001811982, 760823877034573864]

dotenv.load_dotenv()
os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True" 

CONFIG = dotenv_values("config.env")
TOKEN = CONFIG.get("TOKEN")
DB_URL = CONFIG.get("DB_URL")

Timestamp = datetime.datetime.now(datetime.timezone.utc)

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
    """Geralt's custom sub - class"""
    
    def dev_check(self, bot, dev : typing.Union[discord.Member, discord.User]):
        return (dev == dev.id in Geralt.owner_ids)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            status = discord.Status.online,
            intents = discord.Intents.all(),
            activity = discord.Activity(type = discord.ActivityType.playing, name = "Waking up to Die"),
            command_prefix = self.get_prefix,
            case_insensitive = True,
            strip_after_prefix = True,)
        
        self.pfp = CONFIG.get("PFP")
        self.colour = discord.Colour.from_rgb(117, 128, 219)
        self.datetime = discord.utils.format_dt        
        self.mentions = discord.AllowedMentions.none()
        self.owner_ids = DEVELOPER_IDS
        self.default_prefix = ".g"
        self.add_persistent_views = False
        self.description = "I'm Back Bitches"
        
        self.prefixes = {} # Caching the prefixing so it doesn't query the DB each time a command is called.

    async def get_prefix(self, message):
        guild_id = getattr(message.guild, "id", message.author.id)
        if (prefix := self.prefixes.get(guild_id)) is None:
            data = await self.db.fetchrow("SELECT guild_prefix FROM custom_prefix WHERE guild_id = $1", guild_id)
            prefix = self.default_prefix if data is None else data["guild_prefix"]
        return prefix

    async def setup_hook(self) -> None:
        print(f"{colour.Fore.BLUE}-> {time.strftime('%c', time.localtime())} ─ Loading all Extensions.{colour.Style.RESET_ALL}")
        for extensions in COGS_EXTENSIONS:
            try:
                await self.load_extension(extensions)
            except Exception as exception:
                print(f"{colour.Fore.LIGHTRED_EX}-> {time.strftime('%c', time.localtime())} ─ {exception} : {exception} {colour.Style.RESET_ALL}\n")
        
        print(f"{colour.Fore.GREEN}-> {time.strftime('%c', time.localtime())} ─ Extensions Successfully Loaded. {colour.Style.RESET_ALL}")

    async def on_ready(self):
        if not self.add_persistent_views:
            self.add_view(Interface.Info(commands.context, commands.Bot))
            self.add_persistent_views = True    
            
        if not hasattr(self, "uptime"):
            self.uptime = discord.utils.utcnow()
        
        async with aiohttp.ClientSession() as session:
            wbhk = discord.Webhook.partial(id = CONFIG.get("NOTIF_ID"), token = CONFIG.get("NOTIF_TOKEN"), session = session)
            await self.change_presence(
                status = discord.Status.idle,
                activity = discord.Activity(type = discord.ActivityType.listening, name = f".ghelp")) 
            await wbhk.send(f"|| Break Point ||\n───\n<:GeraltRightArrow:904740634982760459> Came alive at ─ {self.datetime(discord.utils.utcnow(), style = 'F')} Hi <a:Waves:920726389869641748>\n```prolog\nNo. of Users ─ {len(list(self.get_all_members()))}\nNo. of Guilds ─ {len(self.guilds)}\nWoke up at ─ {time.strftime('%c', time.gmtime())}```")
            print(f"{colour.Fore.GREEN}-> {time.strftime('%c', time.localtime())} ─ Awakened {colour.Style.RESET_ALL}")
            await session.close()

Geralt = Geralt()

async def run():
    async with Geralt:
        Geralt.loop.create_task(db_connect())
        await Geralt.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(run())