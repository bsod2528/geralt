import json
import discord 
import asyncpg
import aiohttp
import datetime

from discord.ext import commands
from discord.webhook.async_ import Webhook
from Kernel.Utilities.Essential import DB_FUNCS

COGS_EXTENSIONS    =   [
    "Cogs.Misc"
]

KERNEL  =   json.load(open("Kernel\Credentials\Config.json"))
TOKEN   =   KERNEL["Tokens"]["Discord"]
DB_URL  =   KERNEL["DB"]["URL"]
EMOTE   =   json.load(open("Kernel\Credentials\Emotes.json"))

Timestamp   =   datetime.datetime.now(datetime.timezone.utc)

async def DB_CONNECT(): 
    try:
        Geralt.DB    =  await asyncpg.create_pool(dsn = DB_URL)
        print("Connected to the database")
    except Exception as EXCEPTION:
        print(f"Couldnt connect due to {EXCEPTION}")

class Geralt(commands.Bot):
    """Geralt's custom sub - class"""
    def __init__(self, *ARGS, **KWARGS) -> None:
        
        super().__init__(
            Intents =   discord.Intents.all(),
            status  =   discord.Status.do_not_disturb,
            command_prefix  =  commands.when_mentioned_or(KERNEL["Init"]["Prefix"]),
            activity    =   discord.Activity(type = discord.ActivityType.playing, name = "Waking up to Die"))

        self.Kernel =   KERNEL
        self.DT =   discord.utils.format_dt
        self.PFP    =   KERNEL["Init"]["PFP"]
        self.description    =   KERNEL["Init"]["Description"]
        self.colour  =   discord.Colour.from_rgb(117, 128, 219)
        self.Timestamp  =   datetime.datetime.now(datetime.timezone.utc)

        for COGS in COGS_EXTENSIONS:
            try:
                self.load_extension(COGS)
            except Exception as e:
                print(f"Failed to load extension {COGS}\n{type(e).__name__}: {e}")

    async def RELOAD(self, *, COGS : str):
        self.session    =   aiohttp.ClientSession()
        self.WEBHOOK  =   Webhook.from_url(KERNEL["Tokens"]["Discord_WebHook"], session = self.session)
        for COGS in COGS_EXTENSIONS:
            try:
                self.reload_extension(COGS)
            except Exception as EXCEPTION:
                self.WEBHOOK.send(f"{COGS} wasn't able to be reloaded")
        
    async def LOAD(self, *, COGS : str):
        self.session    =   aiohttp.ClientSession()
        self.WEBHOOK  =   Webhook.from_url(KERNEL["Tokens"]["Discord_WebHook"], session = self.session)
        for COGS in COGS_EXTENSIONS:
            try:
                self.load_extension(COGS)
            except Exception as EXCEPTION:
                self.WEBHOOK.send(f"{COGS} wasn't able to be loaded")
    
    async def UNLOAD(self, *, COGS : str):
        self.session    =   aiohttp.ClientSession()
        self.WEBHOOK  =   Webhook.from_url(KERNEL["Tokens"]["Discord_WebHook"], session = self.session)
        for COGS in COGS_EXTENSIONS:
            try:
                self.unload_extension(COGS)
            except Exception as EXCEPTION:
                self.WEBHOOK.send(f"{COGS} wasn't able to be unloaded")
    
    async def on_ready(self):
        self.session    =   aiohttp.ClientSession()
        self.WEBHOOK  =   Webhook.from_url(KERNEL["Tokens"]["Discord_WebHook"], session = self.session)
        await self.change_presence(
            status  =   discord.Status.idle,
            activity    =   discord.Activity(type = discord.ActivityType.listening, name = ".ghelp")) 
        await self.WEBHOOK.send(f"<:replytop:925219706879758406> - Came alive as **{self.user}**\n<:reply:897151692737486949> - {self.DT(self.Timestamp, style = 'F')}")

    def RUN(self):
        super().run(TOKEN, reconnect = True)
 
if __name__ == "__main__":
    Geralt = Geralt()
    Geralt.loop.run_until_complete(DB_CONNECT())
    Geralt.RUN()