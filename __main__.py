import os
import time
import dotenv
import typing
import discord
import asyncpg
import aiohttp
import datetime
import colorama as colour

from dotenv import dotenv_values
from discord.ext import commands    
from discord.webhook.async_ import Webhook

import Source.Kernel.Views.Interface as Interface 

COGS_EXTENSIONS    =   [    
    "Source.Cogs.Fun",
    "Source.Cogs.Help",
    "Source.Cogs.Misc",
    "Source.Cogs.Guild",
    "Source.Cogs.Events",
    "Source.Cogs.Utility",
    "Source.Cogs.Developer",
    "Source.Cogs.Moderation",
    "Source.Cogs.ErrorHandler"
]
                    # FrostiiWeeb#8373   # BSOD#2528 [ ME ]  # SID#0007
DEVELOPER_IDS   =   [746807014658801704, 750979369001811982, 760823877034573864]

dotenv.load_dotenv()
os.environ["JISHAKU_HIDE"] = "True"

CONFIG  =   dotenv_values(".env")
TOKEN   =   CONFIG.get("TOKEN")
DB_URL  =   CONFIG.get("DB_URL")

Timestamp   =   datetime.datetime.now(datetime.timezone.utc)

colour.init()

async def db_connect(): 
    try:
        print(colour.Fore.BLUE + f"-> {time.strftime('%c', time.gmtime())} - Establishing connection with my database." + colour.Style.RESET_ALL)
        Geralt.db    =  await asyncpg.create_pool(dsn = DB_URL)
        print(colour.Fore.GREEN + f"-> {time.strftime('%c', time.gmtime())} - Connection established successfully." + colour.Style.RESET_ALL)
    except Exception as EXCEPTION:
        print(colour.Fore.RED + f"-> {time.strftime('%c', time.gmtime())} - Couldnt connect due to : {EXCEPTION}" + colour.Style.RESET_ALL)

async def create_session():
    Geralt.session  =   aiohttp.ClientSession()

class Geralt(commands.Bot):
    """Geralt's custom sub - class"""
    
    def dev_check(self, bot, dev : typing.Union[discord.Member, discord.User]):
        return ( dev == dev.id in Geralt.owner_ids)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            sync_commmands      =   True,
            case_insensitive    =   True,
            strip_after_prefix  =   True,
            command_prefix      =   self.get_prefix,
            intents             =   discord.Intents.all(),
            status              =   discord.Status.online,
            activity            =   discord.Activity(type = discord.ActivityType.playing, name = "Waking up to Die"))
        
        self.default_prefix         =   ".g"
        self.add_persistent_views   =   False
        self.owner_ids              =   DEVELOPER_IDS
        self.pfp                    =   CONFIG.get("PFP")
        self.description            =   "I'm Back Bitches"
        self.datetime               =   discord.utils.format_dt        
        self.mentions               =   discord.AllowedMentions.none()
        self.colour                 =   discord.Colour.from_rgb(117, 128, 219)
        
        self.prefixes         =   {} # Caching the prefixing so it doesn't query the DB each time a command is called.

        print(colour.Fore.BLUE + f"-> {time.strftime('%c', time.gmtime())} - Loading all Extensions." + colour.Style.RESET_ALL)
        for extensions in COGS_EXTENSIONS:
            try:
                self.load_extension(extensions)
            except Exception as exception:
                print(colour.Fore.LIGHTRED_EX + f"-> {time.strftime('%c', time.gmtime())} - {exception} : {exception}" + colour.Style.RESET_ALL)
        
        print(colour.Fore.GREEN + f"-> {time.strftime('%c', time.gmtime())} - Extensions Successfully Loaded." + colour.Style.RESET_ALL)

    print(colour.Fore.LIGHTYELLOW_EX + f"-> {time.strftime('%c', time.gmtime())} - Waking up" + colour.Style.RESET_ALL)
    
    async def get_prefix(self, message):
        guild_id  =   getattr(message.guild, "id", message.author.id)
        if (prefix := self.prefixes.get(guild_id)) is None:
            data    =   await self.db.fetchrow("SELECT guild_prefix FROM custom_prefix WHERE guild_id = $1", guild_id)
            prefix  =   self.default_prefix if data is None else data["guild_prefix"]
        return prefix

    async def on_ready(self):
        if not self.add_persistent_views:
            self.add_view(Interface.Info(commands.context, commands.Bot))
            self.add_persistent_views = True
            
        if not hasattr(self, "uptime"):
            self.uptime     =   discord.utils.utcnow()
        
        self.session    =   aiohttp.ClientSession()
        self.wbhk       =   Webhook.from_url(CONFIG.get("NOTIF"), session = self.session)
        await self.change_presence(
            status      =   discord.Status.idle,
            activity    =   discord.Activity(type = discord.ActivityType.listening, name = f".ghelp")) 
        await self.wbhk.send(f"<:Balank:912244138567663627>\n──\n<:GeraltRightArrow:904740634982760459> **Sent at -** {self.datetime(discord.utils.utcnow(), style = 'F')}\n```prolog\nNo. of Users - {len(list(self.get_all_members()))}\nNo. of Guilds - {len(self.guilds)}\nWoke up at - {time.strftime('%c', time.gmtime())}```──\n<:Balank:912244138567663627>")
        print(colour.Fore.GREEN + f"-> {time.strftime('%c', time.gmtime())} - Awakened" + colour.Style.RESET_ALL)
        await self.session.close()

    def run(self):
        super().run(TOKEN, reconnect = True)
 
if __name__ == "__main__":
    Geralt = Geralt()
    Geralt.loop.run_until_complete(db_connect())
    Geralt.run()