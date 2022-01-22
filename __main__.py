import json
import disnake
import asyncpg
import aiohttp
import datetime

from disnake.ext import commands
from disnake.webhook.async_ import Webhook


COGS_EXTENSIONS    =   [
   "Source.Cogs.Fun",
   "Source.Cogs.Misc",
   "Source.Cogs.Slash",
   "Source.Cogs.Utility",
   "Source.Cogs.Developer",
   "Source.Cogs.Moderation",
   "Source.Cogs.ErrorHandler"
]

KERNEL  =   json.load(open(r"Source\Kernel\Credentials\Config.json"))
TOKEN   =   KERNEL["Tokens"]["Discord"]
DB_URL  =   KERNEL["DB"]["URL"]

Timestamp   =   datetime.datetime.now(datetime.timezone.utc)

async def DB_CONNECT(): 
    try:
        Geralt.DB    =  await asyncpg.create_pool(dsn = DB_URL)
        print("Connected to the database")
    except Exception as EXCEPTION:
        print(f"Couldnt connect due to : {EXCEPTION}")

class Geralt(commands.Bot):
    """Geralt's custom sub - class"""
    def __init__(self, *ARGS, **KWARGS) -> None:
        super().__init__(
            Intents =   disnake.Intents.members,
            status  =   disnake.Status.online,
            sync_commmands  = True,
            command_prefix  =  commands.when_mentioned_or(KERNEL["Init"]["Prefix"]),
            activity    =   disnake.Activity(type = disnake.ActivityType.playing, name = "Waking up to Die"))

        self.Kernel         =   KERNEL
        self.PFP            =   KERNEL["Init"]["PFP"]
        self.DT             =   disnake.utils.format_dt        
        self.description    =   KERNEL["Init"]["Description"]
        self.Mention        =   disnake.AllowedMentions.none()
        self.colour         =   disnake.Colour.from_rgb(117, 128, 219)
        self.Timestamp      =   datetime.datetime.now(datetime.timezone.utc)

        for COGS in COGS_EXTENSIONS:
            try:
                self.load_extension(COGS)
            except Exception as EXCEPT:
                print(f"{COGS} : {EXCEPT}")
    
    async def on_ready(self):
        if not hasattr(self, "uptime"):
            self.uptime     =   disnake.utils.utcnow()
        self.session    =   aiohttp.ClientSession()
        self.WEBHOOK    =   Webhook.from_url(KERNEL["Tokens"]["Discord_WebHook"], session = self.session)
        await self.change_presence(
            status  =   disnake.Status.idle,
            activity    =   disnake.Activity(type = disnake.ActivityType.listening, name = ".ghelp")) 
        await self.WEBHOOK.send(f"<:ReplyTop:931694333009207387>  - Came alive as **{self.user}**\n<:Reply:930634822865547294> - {self.DT(self.Timestamp, style = 'F')}")

    def RUN(self):
        super().run(TOKEN, reconnect = True)
 
if __name__ == "__main__":
    Geralt = Geralt()
    Geralt.loop.run_until_complete(DB_CONNECT())
    Geralt.RUN()