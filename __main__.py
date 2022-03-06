import os
import time
import dotenv
import typing
import discord
import asyncpg
import aiohttp
import datetime
import colorama as COLOUR

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

COLOUR.init()

async def DB_CONNECT(): 
    try:
        print(COLOUR.Fore.BLUE + f"-> {time.strftime('%c', time.gmtime())} - Establishing connection with my database." + COLOUR.Style.RESET_ALL)
        Geralt.DB    =  await asyncpg.create_pool(dsn = DB_URL)
        print(COLOUR.Fore.GREEN + f"-> {time.strftime('%c', time.gmtime())} - Connection established successfully." + COLOUR.Style.RESET_ALL)
    except Exception as EXCEPTION:
        print(COLOUR.Fore.RED + f"-> {time.strftime('%c', time.gmtime())} - Couldnt connect due to : {EXCEPTION}" + COLOUR.Style.RESET_ALL)

async def SESSION_CREATE():
    Geralt.session  =   aiohttp.ClientSession()

class Geralt(commands.Bot):
    """Geralt's custom sub - class"""
    
    def DEV_CHECK(self, bot, DEV : typing.Union[discord.Member, discord.User]):
        return ( DEV == DEV.id in Geralt.owner_ids)

    def __init__(self, *ARGS, **KWARGS) -> None:
        super().__init__(
            sync_commmands      =   True,
            case_insensitive    =   True,
            strip_after_prefix  =   True,
            command_prefix      =   self.get_prefix,
            intents             =   discord.Intents.all(),
            status              =   discord.Status.online,
            activity            =   discord.Activity(type = discord.ActivityType.playing, name = "Waking up to Die"))
        
        self.DP             =   ".g"
        self.PVA            =   False
        self.owner_ids      =   DEVELOPER_IDS
        self.PFP            =   CONFIG.get("PFP")
        self.description    =   "I'm Back Bitches"
        self.DT             =   discord.utils.format_dt        
        self.Mention        =   discord.AllowedMentions.none()
        self.colour         =   discord.Colour.from_rgb(117, 128, 219)
        
        self.prefixes         =   {} # Caching the prefixing so it doesn't query the DB each time a command is called.

        print(COLOUR.Fore.BLUE + f"-> {time.strftime('%c', time.gmtime())} - Loading all Cogs." + COLOUR.Style.RESET_ALL)
        for COGS in COGS_EXTENSIONS:
            try:
                self.load_extension(COGS)
            except Exception as EXCEPT:
                print(COLOUR.Fore.LIGHTRED_EX + f"-> {time.strftime('%c', time.gmtime())} - {COGS} : {EXCEPT}" + COLOUR.Style.RESET_ALL)
        
        print(COLOUR.Fore.GREEN + f"-> {time.strftime('%c', time.gmtime())} - Cogs Successfully Loaded." + COLOUR.Style.RESET_ALL)

    print(COLOUR.Fore.LIGHTYELLOW_EX + f"-> {time.strftime('%c', time.gmtime())} - Waking up" + COLOUR.Style.RESET_ALL)
    
    async def get_prefix(self, MESSAGE):
        ID  =   getattr(MESSAGE.guild, "id", MESSAGE.author.id)

        if (PREFIX := self.prefixes.get(ID)) is None:
            DATA    =   await self.DB.fetchrow("SELECT guild_prefix FROM custom_prefix WHERE guild_id = $1", ID)
            PREFIX  =   self.DP if DATA is None else DATA["guild_prefix"]
        return PREFIX

    async def on_ready(self):
        if not self.PVA:
            self.add_view(Interface.Info(commands.context, commands.Bot))
            self.PVA = True
            
        if not hasattr(self, "uptime"):
            self.uptime     =   discord.utils.utcnow()
        
        self.session    =   aiohttp.ClientSession()
        self.WEBHOOK    =   Webhook.from_url(CONFIG.get("NOTIF"), session = self.session)
        await self.change_presence(
            status  =   discord.Status.idle,
            activity    =   discord.Activity(type = discord.ActivityType.listening, name = f".ghelp")) 
        await self.WEBHOOK.send(f"<:Balank:912244138567663627>\n──\n<:GeraltRightArrow:904740634982760459> **Sent at -** {self.DT(discord.utils.utcnow(), style = 'F')}\n```prolog\nNo. of Users - {len(list(self.get_all_members()))}\nNo. of Guilds - {len(self.guilds)}\nWoke up at - {time.strftime('%c', time.gmtime())}```──\n<:Balank:912244138567663627>")
        print(COLOUR.Fore.GREEN + f"-> {time.strftime('%c', time.gmtime())} - Awakened" + COLOUR.Style.RESET_ALL)
        await self.session.close()

    def RUN(self):
        super().run(TOKEN, reconnect = True)
 
if __name__ == "__main__":
    Geralt = Geralt()
    Geralt.loop.run_until_complete(DB_CONNECT())
    Geralt.RUN()