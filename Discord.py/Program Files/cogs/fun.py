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
    @commands.command(
        name = 'dm', 
        help = f'```ini\n[ Syntax : .gdm <user/id> <message> ]\n```\n>>> **USE :** What can you not understand by the term\n**AKA :** None present ;)', 
        brief = 'DM')
    async def dm(self, ctx, user : discord.User, *, msg):
        async with ctx.typing():
            await asyncio.sleep(0.5)
            await ctx.send('Done')
        await user.send(f'{msg}')
        
#---ghost ping---#
    @commands.command(
        aliases = ['gp', 'gping'], 
        help = f'```ini\n[ Syntax : .gghost <mention user> ]\n```\n>>> **USE :**Have fun ghost pinging your friends\n**AKA :** `gping` `gp`', 
        brief = 'Use it to ghost ping!')
    async def ghost(self, ctx, member : discord.Member):
        emote = json.load(open('D:\AV\PC\Coding\Discord Bot\Geralt\Discord.py\Program Files\emote.json'))   
        alpha = [f'{emote["linus"]["kill"]}',
                 f'{emote["linus"]["focboi"]}',
                 f'{emote["linus"]["bruh"]}',
                 f'{emote["peep"]["space"]}',
                 f'{emote["peep"]["tf"]}',
                 f'{emote["peep"]["xtremhmm"]}',
                 f'{emote["random_themed"]["pokikill"]}']
        async with ctx.typing():
            await asyncio.sleep(0.1)
        await ctx.send(f'{member.mention} {random.choice(alpha)}')
        await ctx.channel.purge(limit = 2)

#---choose---#
    @commands.command(
        help = f'```ini\n[ Syntax : .gchoose <opt.1> <opt.2> ]\n```\n>>> **USE :** For when you wanna settle the score some other way\n**AKA :** No aliases present ;)')
    async def choose(self, ctx, *choices: str):
        emote = json.load(open('D:\AV\PC\Coding\Discord Bot\Geralt\Discord.py\Program Files\emote.json'))
        async with ctx.typing():
            await asyncio.sleep(0.5)
        await ctx.reply(f'Well, I choose {random.choice(choices)}')

#---emojify---#
    @commands.command(
        aliases = ['oof', 'umph'],
        help = f'```ini\n[ Syntax : .gemojify <text here> ]\n```\n>>> **USE :** Emphasise your messages !\n**AKA :** `.goof` `.gumph`', 
        brief = 'Send emphasised texts')
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
        
#---8 Ball---#
    @commands.command(
        aliases = ['8ball', '8b'], 
        help = f'```ini\n[ Syntax : .gmagicball <your query> ]\n```\n>>> **USE :** 8ball is here to ruin your life!\n**AKA :** `.g8ball` `.8b`', 
        brief = 'The Classic 8Ball! Test you luck')
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