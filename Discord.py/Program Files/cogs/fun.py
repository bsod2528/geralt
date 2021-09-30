import asyncio
import discord
import random
import aiohttp
import datetime
import json
from discord.embeds import Embed
from discord.ext import commands

class Fun(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
    def av(ctx):
        return ctx.author.id == 750979369001811982

#---dm---#    
    @commands.command(name = 'dm', help = 'Sends out my latency', brief = 'Well well well, Im slow')
    async def dm(self, ctx, user : discord.User, *, msg):
        async with ctx.typing():
            await asyncio.sleep(0.5)
            await ctx.reply(f'Done <:good:877497098612924416>')
        await user.send(f'{msg}')
        
#---ghost ping---#
    @commands.command(aliases = ['gp'], help = 'Have fun pinging your friends', brief = 'Use it to ghost ping!')
    async def ghost(self, ctx, member : discord.Member):
        emote = json.load(open('D:\AV\PC\Coding\Discord Bot\Geralt\Discord.py\Program Files\emote.json'))   
        async with ctx.typing():
            await asyncio.sleep(0.1)
        await ctx.send(f'{member.mention} {emote["linuskill"]}')
        await ctx.channel.purge(limit = 2)
    
    @ghost.error
    async def ghost_error(self, ctx, error):
        emote = json.load(open('D:\AV\PC\Coding\Discord Bot\Geralt\Discord.py\Program Files\emote.json'))
        async with ctx.typing():
            await asyncio.sleep(0.5)
        await ctx.reply(f'{emote["trigger"]} Its `.ggp` or `.gghost` and mention the user {emote["linusfb"]}')

#---choose---#
    @commands.command(description='For when you wanna settle the score some other way')
    async def choose(self, ctx, *choices: str):
        emote = json.load(open('D:\AV\PC\Coding\Discord Bot\Geralt\Discord.py\Program Files\emote.json'))
        async with ctx.typing():
            await asyncio.sleep(0.5)
        await ctx.reply(f'Well, I choose {random.choice(choices)}')
    
    @choose.error
    async def choose_error(self, ctx, error):
        emote = json.load(open('D:\AV\PC\Coding\Discord Bot\Geralt\Discord.py\Program Files\emote.json'))
        async with ctx.typing():
            await asyncio.sleep(0.5)
        await ctx.reply(f'You asked me to fricking choose something! Apparently I cant find any items to choose from {emote["hmm"]}')

#---emojify---#
    @commands.command(help = 'Bold texts', brief = 'Send emphasised texts')
    async def emojify(self,ctx, *, text):
        emojis = []
        for s in text:
            if s.isdecimal():
                nte = {'0':'zero','1':'one','2':'two',
                           '3':'three','4':'four','5':'five',
                           '6':'six','7':'seven','8':'eight',
                        '9':'nine'}
                emojis.append(f':{nte.get(s)}:')
            elif s.isalpha():
                emojis.append(f':regional_indicator_{s}:')
            else:
                    emojis.append(s)
        async with ctx.typing():
            await asyncio.sleep(0.5)
            await ctx.send(''.join(emojis))
    
    @emojify.error
    async def emojify_error(self, ctx, error):
        emote = json.load(open('D:\AV\PC\Coding\Discord Bot\Geralt\Discord.py\Program Files\emote.json'))
        async with ctx.typing():
            await asyncio.sleep(0.5)
        emoticon = [f'{emote["linusbruh"]}',
                    f'{emote["worryrun"]}',
                    f'{emote["whyme"]}',
                    f'{emote["yoo"]}',
                    f'{emote["frogworry"]}',
                    f'{emote["trigger"]}',
                    f'{emote["linuskill"]}']
        await ctx.reply(f'Bruh, type something for me to make into an emoji. {random.choice(emoticon)}')
        
#---8 Ball---#
    @commands.command(aliases = ['8ball'], help = '8ball is here to ruin your life!', brief = 'The Classic 8Ball! Test you luck')
    async def magicball(self, ctx):
        response = ['It is Certain.',
                    'It is decidedly so.',
                    'Without a doubt.',
                    'Yes definitely.',
                    'You may rely on it.',
                    'As I see it, yes.',
                    'Most likely.',
                    'Outlook good.',
                    'Yes.',
                    'Signs point to yes.',
                    'Reply hazy, try again.',
                    'Ask again later.',
                    'Better not tell you now.',
                    'Cannot predict now.',
                    'Concentrate and ask again.',
                    'Dont count on it.',
                    'My reply is no.',
                    'My sources say no.',
                    'Outlook not so good.',
                    'Very doubtful.']
        async with ctx.typing():
            await asyncio.sleep(0.5)      
        await ctx.reply(f'{random.choice(response)}')

def setup(bot):
    bot.add_cog(Fun(bot))