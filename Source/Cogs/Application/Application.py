import time
import disnake  
import datetime
import humanize

from disnake.ext import commands

import Source.Kernel.Utilities.Crucial as CRUCIAL
import Source.Kernel.Views.Interface as Interface

class Application(commands.Cog):
    """Discord Application Commands"""
    def __init__(self, bot):
        self.bot    =   bot
        self.TS         =   disnake.utils.format_dt(datetime.datetime.now(datetime.timezone.utc), style = "F")
    
    @commands.slash_command(
        name        =   "ping",
        description =   "Simply ping them for fun.")
    async def ping(self, user : disnake.Member, interaction : disnake.ApplicationCommandInteraction):
        await interaction.response.send_message(f"{user.mention} you have been ponged by : **{interaction.author}**", ephemeral = False)

    @commands.slash_command(
        name        =   "bonk",
        description =   "Simply bonk them for fun.")
    async def bonk(self, user : disnake.Member, interaction : disnake.ApplicationCommandInteraction, reason : str):
        await interaction.response.send_message(f"{user.mention} you have been <:Bonked:934033408106057738> by : **{interaction.author}**\n**Reason :** {reason}", ephemeral = False)
    
    @commands.slash_command(
        name        =   "uptime",
        description =   "Get the uptime of me :)")
    async def uptime(self, interaction : disnake.ApplicationCommandInteraction):
        TIME    =   disnake.utils.utcnow() - self.bot.uptime
        await interaction.response.send_message(content =   f"<:GeraltRightArrow:904740634982760459> I have been `online` for -\n>>> <:ReplyContinued:930634770004725821> - Exactly : {humanize.precisedelta(TIME)}\n<:Reply:930634822865547294> - Roughly Since : {self.bot.DT(self.bot.uptime, style = 'R')} <a:CoffeeSip:907110027951742996>", ephemeral = True)

    @commands.slash_command(
        name        =   "as",
        description =   "Send a webhook as another user.")
    async def mimic(self, user : disnake.Member, *, message : str, interaction : disnake.ApplicationCommandInteraction):
        WBHK = await CRUCIAL.FETCH_WEBHOOK(interaction.channel)
        thread = disnake.utils.MISSING
        if isinstance(interaction.channel, disnake.Thread):
            thread = interaction.channel
        await WBHK.send(
            message, 
            avatar_url  =   user.display_avatar.url, 
            username    =   user.display_name, 
            thread      =   thread)
        await interaction.response.send_message(content = f"Done **{interaction.author}** <:NanoTick:925271358735257651>", ephemeral = True)
    
    @commands.slash_command(
        name        =   "latency",
        description =   "Get the exact latencies.")
    async def latency(self, interaction : disnake.ApplicationCommandInteraction):
        PING    =   []
        START_DB    =   time.perf_counter()
        await self.bot.DB.fetch("SELECT 1")
        END_DB  =   time.perf_counter()
        DB_PING =   (END_DB - START_DB) * 1000
        PING.append(DB_PING)
        WEBSOCKET_PING   =   self.bot.latency * 1000
        PING.append(WEBSOCKET_PING)
        PING_EMB = disnake.Embed(
            title = "__ My Latencies : __",
            description =   f"""```prolog\n> PostGreSQL     : {round(DB_PING, 1)} ms
> Discord API    : {WEBSOCKET_PING:,.0f} ms```""",
            colour = self.bot.colour)
        PING_EMB.timestamp = disnake.utils.utcnow()
        await interaction.response.send_message(embed = PING_EMB, ephemeral = True)

    @commands.slash_command(
        name        =   "stupidity-survey",
        description =   "Simple survey showcasing how stupid you are.")
    async def stupidity(self, INTERACTION : disnake.ApplicationCommandInteraction):
        await INTERACTION.response.send_modal(modal = Interface.Modal(self.bot))

def setup(bot):
    bot.add_cog(Application(bot))