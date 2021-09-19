import discord
import os
import datetime
import asyncio
import random
from discord import interactions
from googleapiclient.discovery import build
from discord.ext import commands

api_key = 'AIzaSyBEed4XMr_rS8y6LcdEFBmw3CCR7oLALXk'

class Utility(commands.Cog, discord.ui.View):

    def __init__ (self, bot):
        self.bot = bot
    
#---latency---#
    @commands.command(name = 'ping', help = 'Sends out bot latency!', brief = 'Well, nvm!')
    async def ping(self, ctx):
        async with ctx.typing():
            await asyncio.sleep(0.5)
        await ctx.reply(f'Pong! My latency `{self.bot.latency*1000:,.0f}`ms.')    
        await ctx.add_reaction('🏓')    

#---search pic---#
    @commands.command(name = 'pic', help = 'Wanna show an example?', brief = 'Get an image from Google Images!')
    async def pic(self, ctx, *search):
        ran = random.randint(0,9)
        resource = build('customsearch', 'v1', developerKey = api_key).cse()
        result = resource.list(q = f'{search}', cx = 'de0a8ba5eccedba09', searchType = 'image').execute()
        url = result['items'][ran]['link']
        emb = discord.Embed(
            title = f'Here is your Image',
            color = ctx.author.color)
        emb.timestamp = datetime.datetime.now(datetime.timezone.utc)
        emb.set_image(url = url)
        await ctx.reply(embed = emb)

#---web search---#
    @commands.command(name = 'web', help = 'Wanna find something quickly?', brief = 'Searches Google for you!')
    async def web(self, ctx,*search):
        page = 3
        resource = build("customsearch", "v1", developerKey=api_key).cse()
        images = []
        strsAPPEND = ""
        for i in range(1, page, 5):
            result=resource.list(q=f"{search}",cx="de0a8ba5eccedba09",start=i).execute()
            images += result["items"]
    
        for item in images:
    
            imagesNEW = " \n+ " + item["title"]
            link = "{0} : {1}".format(imagesNEW, item["link"])
            strsAPPEND += link
            embed1 = discord.Embed(
                title = f"Here your web list ",
                description = f"List:\n{strsAPPEND}",
                color = ctx.author.color,
            )
        await ctx.reply(embed=embed1)

#---nice---#
    @commands.command(name = '69', help = 'Nice', brief = 'Nice')
    async def nice(self, ctx):
        async with ctx.typing():
            await asyncio.sleep(0.5)
        emb = discord.Embed(
            title = '42069',
            description = '42069',
        color = ctx.author.color)
        emb.add_field(
            name = '42069',
            value = '42069')
        emb.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await ctx.reply(embed = emb)
    
def setup(bot):
    bot.add_cog(Utility(bot))