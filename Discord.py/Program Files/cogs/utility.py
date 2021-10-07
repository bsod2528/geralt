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

#---about me---#
    @commands.command(
        name = "about", 
        help = f"```ini\n[ Syntax : .gabout ]\n```\n>>> **USE :** Elaborate details about me\n**AKA :** `.ginfo` `.gbotinfo`", 
        brief = "Get Bot Info", 
        aliases = ['info', "botinfo"])
    @commands.guild_only()
    async def about(self, ctx):
        emote = json.load(open('D:\AV\PC\Coding\Discord Bot\Geralt\Discord.py\Program Files\emote.json'))
        dev = self.bot.get_user(750979369001811982)
        colour = discord.Color.from_rgb(117, 128, 219)
        embed = discord.Embed(title = "Geralt : The Bot", description = f"Geralt is a simple moderation + fun bot to have in your discord server ! You can invite me to your server by going to my website, and join my support server. This bot is made and maintained by **[{dev}]({dev.avatar})**\n\u200b", colour = colour)
        embed.set_thumbnail(url = ctx.me.avatar)
        embed.add_field(
            name = "Coded in:",
            value=f"**Language:** **[`python 3.9.7`](https://www.python.org/)**\n**Library:** **[`discord.py 2.0`](https://github.com/Rapptz/discord.py)**\nㅤㅤㅤㅤ\U00002514 Master Branch")
        embed.add_field(
            name = "Statistics:",
            value=f"**Servers:** `{len([g.id for g in self.bot.guilds])}`\n**Users:** `{len([g.id for g in self.bot.users])}`", inline = True)
        embed.add_field(
            name = "On Discord Since:",
            value=f"<t:{round(ctx.me.created_at.timestamp())}:D>")
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            style = discord.ButtonStyle.link, 
            url = 'https://bsod2528.wixsite.com/geralt', 
            label = 'Geralt | Home', 
            emoji = f'{emote["panda"]["cool"]}'))
        view.add_item(discord.ui.Button(
            style = discord.ButtonStyle.link,
            label = 'Geralt | Support',
            url = 'https://discord.gg/JXEu2AcV5Y',
            emoji = f'{emote["panda"]["clap"]}'))
        view.add_item(discord.ui.Button(
            style = discord.ButtonStyle.link,
            label = 'Source | Github',
            url = 'https://github.com/BSOD2528/Geralt',
            emoji = f'{emote["panda"]["blob"]}'))
        async with ctx.typing():
            await asyncio.sleep(0.5)
        await ctx.send(embed = embed, view = view)

#---latency---#
    @commands.command(
        name = 'ping', 
        help = f'```ini\n[ Syntax : .gping ]\n```\n>>> **USE :** Sends out my latency!\n**AKA :** No aliases present ;)', 
        brief = 'Well, Im slow')
    async def ping(self, ctx):
        async with ctx.typing():
            await asyncio.sleep(0.5)
        await ctx.reply(f'Pong! My latency `{self.bot.latency*1000:,.0f}ms`.')      

#---search pic---#
    @commands.command(
        name = 'images', 
        help = f'```ini\n[ Syntax : .gimages <image keyword> ]\n```\n>>> **USE :** Search Google images\n**AKA :** `.gpic`', 
        brief = 'Get an image from Google Images!',
        aliases = ['pic'])
    async def images(self, ctx, *search):
        apikey = json.load(open(r'D:\AV\PC\Coding\Discord Bot\Geralt\Discord.py\Program Files\config.json'))
        ran = random.randint(0,9)
        resource = build('customsearch', 'v1', developerKey = api_key).cse()
        result = resource.list(q = f'{search}', cx = f'{apikey["API"]}', searchType = 'image').execute()
        url = result['items'][ran]['link']
        emb = discord.Embed(
            title = f'Here is your Image',
            color = discord.Color.from_rgb(117, 128, 219))
        emb.timestamp = datetime.datetime.now(datetime.timezone.utc)
        emb.set_image(url = url)
        await ctx.reply(embed = emb)

#---web search---#
    @commands.command(
        name = 'web', 
        help = f'```ini\n[ Syntax : .gweb <search keyword> ]\n```\n>>> **USE :** Wanna find something quickly? Search Google!\n**AKA :** `.gsearch` `.ggoogle`', 
        brief = 'Searches Google for you!',
        aliases = ['search','google'])
    async def web(self, ctx,*search):
        apikeyy = json.load(open(r'D:\AV\PC\Coding\Discord Bot\Geralt\Discord.py\Program Files\config.json'))
        page = 3
        resource = build("customsearch", "v1", developerKey=api_key).cse()
        images = []
        strsAPPEND = ""
        for i in range(1, page, 5):
            result=resource.list(q=f"{search}", cx=f'{apikeyy["API"]}',start=i).execute()
            images += result["items"]
    
        for item in images:
    
            imagesNEW = " \n+ " + item["title"]
            link = "{0} : {1}".format(imagesNEW, item["link"])
            strsAPPEND += link
            embed1 = discord.Embed(
                title = f"Here your web list ",
                description = f"List:\n{strsAPPEND}",
                color = discord.Color.from_rgb(117, 128, 219),
            )
        async with ctx.typing():
            await asyncio.sleep(0.5)
        await ctx.reply(embed=embed1)

#---nice---#
    @commands.command(
        name = 'nice', 
        help = f'```ini\[ Syntax : .gnice ]\n```\n>>> **USE :** Nice\n**AKA :** `.g69`', brief = 'Nice')
    async def nice(self, ctx):
        async with ctx.typing():
            await asyncio.sleep(0.5)
        emb = discord.Embed(
            title = '42069',
            description = '42069',
        color = discord.Color.from_rgb(117, 128, 219))
        emb.add_field(
            name = '42069',
            value = '42069')
        emb.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await ctx.reply(embed = emb)
    
def setup(bot):
    bot.add_cog(Utility(bot))