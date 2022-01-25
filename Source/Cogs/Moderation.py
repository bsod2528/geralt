import disnake
import aiohttp
import datetime

from disnake.ext import commands

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot    =   bot
        self.TO     =   aiohttp.ClientSession()
    
        async def before_timeout(*, USER : int, GUILD : int, TIME):
            Timeout_Duration    =   (datetime.datetime.utcnow() + datetime.timedelta(minutes =   TIME)).isoformat()
            Header              =   {"Authorization :" f"Bot {self.bot.http.token}"}
            URL                 =   f"https://discord.com/api/v9/guilds/{GUILD}/members/{USER}"
            Timeout             =   Timeout_Duration
            Json_Value          =   {"communications_disabled_until"    :   Timeout}
            async with self.TO(URL, json = Json_Value, headers = Header):
                pass
            
    @commands.command()
    @commands.is_owner()
    async def timeout(self, ctx, guild : disnake.Guild, USER : disnake.Member):
        pass

def setup(bot):
    bot.add_cog(Moderation(bot))