import discord
import os
import datetime
import asyncio
import random
import json
import threading
import asyncpg
from discord import interactions
from googleapiclient.discovery import build
from discord.ext import commands

api_key = 'AIzaSyBEed4XMr_rS8y6LcdEFBmw3CCR7oLALXk'

class Utility(commands.Cog, discord.ui.View):
    

    def __init__ (self, bot):
        self.bot = bot
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)
        self.color = discord.Color.from_rgb(117, 128, 219)
        self.emote = json.load(open('Program Files\Emotes.json'))   
    
    @commands.command(
        name = 'avatar',
        aliases = ['pfp'],
        help = f'```ini\n[ Syntax : .gavatar [member mention/id] ]\n```\n>>> **USE :** Gets the Avatar of a user or you!\n**AKA :** `.gpfp`'
    )
    async def avatar(self, ctx, *, user : discord.Member = None):
        emb = discord.Embed(
            color = self.color)
        user = user or ctx.author
        avatar = user.display_avatar.with_static_format('png')
        emb.set_author(
            name = f'PFP of - {str(user)}', 
            url = avatar)
        emb.set_image(url = avatar)
        emb.timestamp = self.timestamp
        await ctx.send(embed = emb)
    
    @commands.command( 
        help = f'```ini\n[ Syntax : .gabout ]\n```\n>>> **USE :** Elaborate details about me\n**AKA :** `.ginfo` `.gbotinfo`', 
        brief = 'Get Bot Info', 
        aliases = ['about', 'botinfo'])
    @commands.guild_only()
    async def info(self, ctx):
        dev = self.bot.get_user(750979369001811982)
        emb = discord.Embed(
            title = "Geralt : Da Bot <:WinGIT:898591166864441345>", 
            description = f'Geralt is a simple moderation + fun bot to have in your discord server <:AkkoDab:898610956895154288> You can invite me to your server by going to my website, and join my support server. This bot is made and maintained by **[{dev}]({dev.avatar})**\n\u200b', 
            colour = self.color)
        emb.set_thumbnail(url = ctx.me.avatar)
        emb.add_field(
            name = 'Coded in:',
            value=f'**Language :** **[`python 3.10.0`](https://www.python.org/)** <:WinTerminal:898609124982554635> \n**Library :** **[`discord.py 2.0`](https://github.com/Rapptz/discord.py)** <:WinPython:898614277018124308>\nㅤㅤㅤㅤ<:reply:897151692737486949> Master Branch')
        emb.add_field(
            name = 'Statistics:',
            value=f'**Servers :** `{len([g.id for g in self.bot.guilds])}`\n**Users :** `{len([g.id for g in self.bot.users])}`', inline = True)
        emb.add_field(
            name = "On Discord Since :",
            value=f'<t:{round(ctx.me.created_at.timestamp())}:D> <:WinBlush:898571239755489330>')
        emb.timestamp = self.timestamp
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            style = discord.ButtonStyle.link, 
            url = 'https://bsod2528.wixsite.com/geralt', 
            label = 'Geralt | Home', 
            emoji = f'{self.emote["panda"]["cool"]}'))
        view.add_item(discord.ui.Button(
            style = discord.ButtonStyle.link,
            label = 'Geralt | Support',
            url = 'https://discord.gg/JXEu2AcV5Y',
            emoji = f'{self.emote["panda"]["clap"]}'))
        async with ctx.typing():
            await asyncio.sleep(0.5)
        await ctx.reply(embed = emb, view = view)

    @commands.command(
        name = 'ping',
        aliases = ['pong'],
        help = f'```ini\n[ Syntax : .gping ]\n```\n>>> **USE :** Sends out my latency!\n**AKA :** `.gpong`', 
        brief = 'Well, Im slow')
    async def ping(self, ctx):
        async with ctx.typing():
            await asyncio.sleep(0.5)
        message = await ctx.reply(f'`Checking .` <a:WinLoad:898571559265001513>')      
        await message.edit(content = f'`Checking . .` <a:WinLoad:898571559265001513>')
        await message.edit(content = f'`Checking . . .` <a:WinLoad:898571559265001513>')
        await message.edit(content = f'`Checking . . . .` <a:WinLoad:898571559265001513>')
        await message.edit(content = f'`Websocket - {self.bot.latency*1000:,.0f}ms`')

    @commands.command(
        name = 'image', 
        help = f'```ini\n[ Syntax : .gimages <image keyword> ]\n```\n>>> **USE :** Search Google images\n**AKA :** `.gpic`', 
        brief = 'Get an image from Google Images!',
        aliases = ['pic'])
    async def image (self, ctx, *search):
        apikey = json.load(open('Program Files\Key.json'))   

        ran = random.randint(0,9)
        resource = build('customsearch', 'v1', developerKey = api_key).cse()
        result = resource.list(q = f'{search}', cx = f'{apikey["API"]}', searchType = 'image').execute()
        url = result['items'][ran]['link']
        emb = discord.Embed(
            title = f'Your Choice of Image',
            color = self.color)
        emb.timestamp = self.timestamp
        emb.set_image(url = url)
        await ctx.reply(embed = emb)

    @commands.command(
        name = 'web', 
        help = f'```ini\n[ Syntax : .gweb <search keyword> ]\n```\n>>> **USE :** Wanna find something quickly? Search Google!\n**AKA :** `.gsearch` `.ggoogle`', 
        brief = 'Searches Google for you!',
        aliases = ['search','google'])
    async def web(self, ctx,*search):
        apikeyy = json.load(open('Program Files\Key.json'))   
        page = 3
        resource = build('customsearch', 'v1', developerKey = api_key).cse()
        images = []
        strsAPPEND = ""
        for i in range(1, page, 5):
            result=resource.list(
                q = f'{search}', 
                cx = f'{apikeyy["API"]}',
                start = i).execute()
            images += result["items"]
    
        for item in images:
    
            imagesNEW = '\n<:reply:897151692737486949>' + item["title"]
            link = '{0} : {1}'.format(imagesNEW, item["link"])
            strsAPPEND += f'{link}'
            emb = discord.Embed(
                title = f'Your search results below',
                description = f'\n{strsAPPEND}',
                color = self.color)
            emb.timestamp = self.timestamp
        async with ctx.typing():
            await asyncio.sleep(0.5)
        await ctx.reply(embed=emb)

    @commands.command(
        name = 'nice', 
        help = f'```ini\[ Syntax : .gnice ]\n```\n>>> **USE :** Nice\n**AKA :** `.g69`', 
        brief = 'Nice')
    async def nice(self, ctx):
        async with ctx.typing():
            await asyncio.sleep(0.5)
        emb = discord.Embed(
            title = '42069',
            description = '42069',
        color = self.color)
        emb.add_field(
            name = '42069',
            value = '42069')
        emb.timestamp = self.timestamp
        await ctx.reply(embed = emb)
    
def setup(bot):
    bot.add_cog(Utility(bot))