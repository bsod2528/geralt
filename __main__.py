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
   "Source.Cogs.Guild",
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

async def DB_CONNECT(): 
    try:
        print("- Establishing connection with my database.")
        Geralt.DB    =  await asyncpg.create_pool(dsn = DB_URL)
        print("- Connection established successfully.")
    except Exception as EXCEPTION:
        print(f"- Couldnt connect due to : {EXCEPTION}")

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

        print("- Loading all Cogs.")
        for COGS in COGS_EXTENSIONS:
            try:
                self.load_extension(COGS)
            except Exception as EXCEPT:
                print(f"- {COGS} : {EXCEPT}")
        
        print("- Cogs Successfully Loaded.")

    print("- Waking up")
    
    async def on_guild_join(self, GUILD):
        """Sends a Webhook upon joining a guild"""
        self.session    =   aiohttp.ClientSession()
        self.WEBHOOK    =   Webhook.from_url(KERNEL["Tokens"]["JoinLog"], session = self.session)
        
        try:
            await self.DB.execute(f"INSERT INTO guild_info (id, name, owner_id) VALUES ($1, $2, $3)", GUILD.id, GUILD.name, GUILD.owner_id)
            print(f"Logged in {GUILD}'s details.")
        except asyncpg.UniqueViolationError:
            print(f"{GUILD}'s information has already been logged in.")

        JOIN_EMB    =   disnake.Embed(
            title   =   f":scroll: I Joined {GUILD.name}",
            colour  =   self.colour)
        JOIN_EMB.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> General Information :",
            value   =   f"> **<:ReplyContinued:930634770004725821> - <a:Owner:905750348457738291> Owner :** {GUILD.owner.mention} (`{GUILD.owner.id}`) \n" \
                        f"> **<:ReplyContinued:930634770004725821> - <a:Info:905750331789561856> Identification No. :** `{GUILD.id}` \n" \
                        f"> **<:Reply:930634822865547294> - <a:Verify:905748402871095336> Verification Level :** {str(GUILD.verification_level).replace('_', ' ').replace('`NONE`', '`NILL`').title()}")
        JOIN_EMB.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> Initialisation :",
            value   =   f"> **<:ReplyContinued:930634770004725821> - <a:Woo:905754435379163176> Made On :** {self.DT(GUILD.created_at)} \n" \
                        f"> **<:Reply:930634822865547294> - <a:WumpusVibe:905457020575031358> I Joined :** {self.DT(disnake.utils.utcnow())}",
            inline  =   False)                
        JOIN_EMB.timestamp  =   disnake.utils.utcnow()
        JOIN_EMB.set_thumbnail(url = GUILD.icon.url)
        await self.WEBHOOK.send(embed = JOIN_EMB)
        await self.session.close()
    
    async def on_guild_remove(self, GUILD):
        """Sends a Webhook upon being removed from a guild"""
        self.session    =   aiohttp.ClientSession()
        self.WEBHOOK    =   Webhook.from_url(KERNEL["Tokens"]["LeaveLog"], session = self.session)
        
        LEAVE_EMB    =   disnake.Embed(
            title   =   f":scroll: I Left {GUILD.name}",
            colour  =   disnake.Colour.from_rgb(255, 97, 142))
        LEAVE_EMB.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> General Information :",
            value   =   f"> **<:ReplyContinued:930634770004725821> - <a:Owner:905750348457738291> Owner :** {GUILD.owner.mention} (`{GUILD.owner.id}`) \n" \
                        f"> **<:ReplyContinued:930634770004725821> - <a:Info:905750331789561856> Identification No. :** `{GUILD.id}` \n" \
                        f"> **<:Reply:930634822865547294> - <a:Verify:905748402871095336> Verification Level :** {str(GUILD.verification_level).replace('_', ' ').replace('`NONE`', '`NILL`').title()} \n")
        LEAVE_EMB.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> Initialisation :",
            value   =   f"> **<:ReplyContinued:930634770004725821> - <a:Woo:905754435379163176> Made On :** {self.DT(GUILD.created_at)} \n" \
                        f"> **<:Reply:930634822865547294> - <a:PAIN:939876989655994488> I Left :** {self.DT(disnake.utils.utcnow())}",
            inline  =   False)                
        LEAVE_EMB.timestamp  =   disnake.utils.utcnow()
        LEAVE_EMB.set_thumbnail(url = GUILD.icon.url)
        await self.WEBHOOK.send(embed = LEAVE_EMB)
        await self.session.close()

    async def on_ready(self):
        if not hasattr(self, "uptime"):
            self.uptime     =   disnake.utils.utcnow()
        self.session    =   aiohttp.ClientSession()
        self.WEBHOOK    =   Webhook.from_url(KERNEL["Tokens"]["Discord_WebHook"], session = self.session)
        await self.change_presence(
            status  =   disnake.Status.idle,
            activity    =   disnake.Activity(type = disnake.ActivityType.listening, name = ".ghelp")) 
        await self.WEBHOOK.send(f"<:ReplyTop:931694333009207387>  - Came alive as **{self.user}**\n<:Reply:930634822865547294> - {self.DT(disnake.utils.utcnow(), style = 'F')}")
        print("- Awakened")
        await self.session.close()

    async def on_slash_command_error(self, interaction : disnake.ApplicationCommandInteraction, error : commands.CommandError):
        ERROR_EMB   =   disnake.Embed(
            title       =   f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED",
            description = f"```py\n{error}\n```<:Reply:930634822865547294> **Occurance :** {self.DT(disnake.utils.utcnow())}",
            colour      = 0x2F3136)
        await interaction.response.send_message(embed = ERROR_EMB, ephemeral = True)
        return

    def RUN(self):
        super().run(TOKEN, reconnect = True)
 
if __name__ == "__main__":
    Geralt = Geralt()
    Geralt.loop.run_until_complete(DB_CONNECT())
    Geralt.RUN()