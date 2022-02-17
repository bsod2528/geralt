import os
import json
import time
import disnake
import asyncpg
import aiohttp
import datetime
import colorama as COLOUR

from disnake.ext import commands    
from disnake.webhook.async_ import Webhook

import Source.Kernel.Views.Interface as Interface 

COGS_EXTENSIONS    =   [
   "jishaku",           
   "Source.Cogs.Fun",
   "Source.Cogs.Misc",
   "Source.Cogs.Guild",
   "Source.Cogs.Events",
   "Source.Cogs.Utility",
   "Source.Cogs.Developer",
   "Source.Cogs.Moderation",
   "Source.Cogs.Application",
   "Source.Cogs.ErrorHandler"
]

os.environ["JISHAKU_HIDE"] = "True"

KERNEL  =   json.load(open(r"Source\Kernel\Credentials\Config.json"))
TOKEN   =   KERNEL["Tokens"]["Discord"]
DB_URL  =   KERNEL["DB"]["URL"]

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
    def __init__(self, *ARGS, **KWARGS) -> None:
        super().__init__(
            intents =   disnake.Intents.all(),
            status  =   disnake.Status.online,
            sync_commmands  = True,
            command_prefix  =  commands.when_mentioned_or(".g"),
            activity    =   disnake.Activity(type = disnake.ActivityType.playing, name = "Waking up to Die"),
            strip_after_prefix  =   True)
        
        self.Kernel         =   KERNEL
        self.owner          =   750979369001811982
        self.PFP            =   KERNEL["Init"]["PFP"]
        self.DT             =   disnake.utils.format_dt        
        self.description    =   KERNEL["Init"]["Description"]
        self.Mention        =   disnake.AllowedMentions.none()
        self.colour         =   disnake.Colour.from_rgb(117, 128, 219)
        self.PVA            =   False

        print(COLOUR.Fore.BLUE + f"-> {time.strftime('%c', time.gmtime())} - Loading all Cogs." + COLOUR.Style.RESET_ALL)
        for COGS in COGS_EXTENSIONS:
            try:
                self.load_extension(COGS)
            except Exception as EXCEPT:
                print(COLOUR.Fore.LIGHTRED_EX + f"-> {time.strftime('%c', time.gmtime())} - {COGS} : {EXCEPT}" + COLOUR.Style.RESET_ALL)
        
        print(COLOUR.Fore.GREEN + f"-> {time.strftime('%c', time.gmtime())} - Cogs Successfully Loaded." + COLOUR.Style.RESET_ALL)

    print(COLOUR.Fore.LIGHTYELLOW_EX + f"-> {time.strftime('%c', time.gmtime())} - Waking up" + COLOUR.Style.RESET_ALL)

    async def on_ready(self):
        if not self.PVA:
            self.add_view(Interface.Info(commands.context, commands.Bot))
            self.PVA = True
            
        if not hasattr(self, "uptime"):
            self.uptime     =   disnake.utils.utcnow()
        self.session    =   aiohttp.ClientSession()
        self.WEBHOOK    =   Webhook.from_url(KERNEL["Tokens"]["Discord_WebHook"], session = self.session)
        await self.change_presence(
            status  =   disnake.Status.idle,
            activity    =   disnake.Activity(type = disnake.ActivityType.listening, name = ".ghelp")) 
        await self.WEBHOOK.send(f"```prolog\nNo. of Users - {len(list(self.get_all_members()))}\nNo. of Guilds - {len(self.guilds)}\nWoke up at - {time.strftime('%c', time.gmtime())}```")
        print(COLOUR.Fore.GREEN + f"-> {time.strftime('%c', time.gmtime())} - Awakened" + COLOUR.Style.RESET_ALL)
        await self.session.close()

    def RUN(self):
        super().run(TOKEN, reconnect = True)
 
if __name__ == "__main__":
    Geralt = Geralt()
    Geralt.loop.run_until_complete(DB_CONNECT())
    Geralt.RUN()