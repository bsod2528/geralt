import discord
import os
import datetime
import asyncio
import random
import json
from discord import interactions
from googleapiclient.discovery import build
from discord.ext import commands

api_key = 'AIzaSyBEed4XMr_rS8y6LcdEFBmw3CCR7oLALXk'

class Utility(commands.Cog, discord.ui.View):

    def __init__ (self, bot):
        self.bot = bot
    emote = json.load(open('D:\AV\PC\Coding\Discord Bot\Geralt\Discord.py\Program Files\emote.json'))

#---about me---#
    @commands.command(name = 'info', help = "View some info about the bot", brief = "Get Bot Info")
    @commands.guild_only()
    async def about(self, ctx):
        dev = self.bot.get_user(750979369001811982)
        colour = ctx.author.color
        emb = discord.Embed(
            title = 'About Me', 
            description = f'Geralt is an amazing and simple bot to roast your friends and to moderate your server! Down below is the button to my webite. Go check it totally to take a look at all my commands and also to invite me into your server. Geralt has been developed and maintained by ****\n\u200b', 
            colour = colour)
        emb.set_thumbnail(url = f'https://cdn.discordapp.com/avatars/873204919593730119/f7fa349c1100489a68a32672e6a55edc.webp?size=128a')
        emb.add_field(
            name = 'Written in:', 
            value = f'**Language:** **[`python 3.8.5`](https://www.python.org/)**\n**Library:** **[`discord.py 2.0`](https://github.com/Rapptz/discord.py)**\nㅤㅤㅤㅤ\U00002514 Master Branch')
        emb.add_field(
            name = 'Stats:',
            value = f'**Servers:** {len([g.id for g in self.bot.guilds])} servers\n**Users:** {len([g.id for g in self.bot.users])}',
            inline = False)
        emb.add_field(
            name = 'On Discord Since',
            value = f'<t:{round(ctx.me.created_at.timestamp())}:D>')
        emb.timestamp = datetime.datetime.now(datetime.timezone.utc)
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            style = discord.ButtonStyle.link, 
            url = 'https://bsod2528.wixsite.com/geralt', 
            label = 'Geralt | Home ', 
            emoji = '<:me:881174571804409886>'))
        view.add_item(discord.ui.Button (
            label = 'Geralt | Support',
            url = 'https://discord.gg/JXEu2AcV5Y'))
        await ctx.send(embed = emb, view = view)

#---latency---#
    @commands.command(name = 'ping', help = 'Sends out bot latency!', brief = 'Well, nvm!')
    async def ping(self, ctx):
        async with ctx.typing():
            await asyncio.sleep(0.5)
        await ctx.reply(f'Pong! My latency `{self.bot.latency*1000:,.0f}ms`.')      

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