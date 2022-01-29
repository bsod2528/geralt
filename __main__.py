import os
import json
import disnake
import asyncpg
import aiohttp
import datetime

from disnake.ext import commands    
from disnake.webhook.async_ import Webhook

COGS_EXTENSIONS    =   [
   "jishaku",           
   "Source.Cogs.Fun",
   "Source.Cogs.Misc",
   "Source.Cogs.Slash",
   "Source.Cogs.Utility",
   "Source.Cogs.Developer",
   "Source.Cogs.Moderation",
   "Source.Cogs.ErrorHandler"
]

os.environ["JISHAKU_HIDE"] = "True"

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
            intents =   disnake.Intents.all(),
            status  =   disnake.Status.online,
            sync_commmands  = True,
            command_prefix  =  commands.when_mentioned_or(KERNEL["Init"]["Prefix"]),
            activity    =   disnake.Activity(type = disnake.ActivityType.playing, name = "Waking up to Die"))

        self.owner          =   750979369001811982
        self.Kernel         =   KERNEL
        self.PFP            =   KERNEL["Init"]["PFP"]
        self.DT             =   disnake.utils.format_dt        
        self.description    =   KERNEL["Init"]["Description"]
        self.Mention        =   disnake.AllowedMentions.none()
        self.colour         =   disnake.Colour.from_rgb(117, 128, 219)

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
        await self.WEBHOOK.send(f"<:ReplyTop:931694333009207387>  - Came alive as **{self.user}**\n<:Reply:930634822865547294> - {self.DT(disnake.utils.utcnow(), style = 'F')}")

    async def on_slash_command_error(self, interaction : disnake.ApplicationCommandInteraction, error : commands.CommandError):
        ERROR_EMB   =   disnake.Embed(
            title       =   f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED",
            description = f"```py\n{error}\n```<:Reply:930634822865547294> **Occurance :** {self.DT(disnake.utils.utcnow())}",
            colour      = 0x2F3136)
        await interaction.response.send_message(embed = ERROR_EMB, ephemeral = True)
        return

    async def CLOSE(self):
        await super().close()
        await self.session.close()

    def RUN(self):
        super().run(TOKEN, reconnect = True)
 
if __name__ == "__main__":
    Geralt = Geralt()
    Geralt.loop.run_until_complete(DB_CONNECT())
    Geralt.RUN()