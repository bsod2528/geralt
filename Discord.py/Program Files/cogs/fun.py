import asyncio
import discord
import random
import aiohttp
import datetime
from discord.embeds import Embed
from discord.ext import commands

class Fun(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
    def av(ctx):
        return ctx.author.id == 750979369001811982

#---dm---#    
    @commands.command()
    async def dm(self, ctx, user : discord.User, *, msg):
        async with ctx.typing():
            await asyncio.sleep(0.5)
            await ctx.send(f'Done <:good:877497098612924416>')
        await user.send(f'{msg}')
        
#---ghost ping---#
    @commands.command(aliases = ['gp'])
    async def ghost(self, ctx, member : discord.Member):
        async with ctx.typing():
            await asyncio.sleep(0.1)
        await ctx.send(f'{member.mention} <:linuskill:886606006761717760>')
        await ctx.channel.purge(limit = 2)
    @ghost.error
    async def ghost_error(self, ctx, error):
        async with ctx.typing():
            await asyncio.sleep(0.5)
        emb = discord.Embed(
            title = 'Command Syntax Error',
            description = f'{ctx.author.mention} YO! <:linuskill:886606006761717760> \n Use `ggp` or `gghost` and mention someone.',
            color = ctx.author.color)
        emb.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed = emb)

#---choose---#
    @commands.command(description='For when you wanna settle the score some other way')
    async def choose(self, ctx, *choices: str):
        async with ctx.typing():
            await asyncio.sleep(0.5)
        emb = discord.Embed(
            title = 'This or That',
            description = f'{ctx.message.author.mention} {random.choice(choices)}',
            color = ctx.author.color)
        emb.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await ctx.send(embed = emb)
    
    @choose.error
    async def choose_error(self, ctx, error):
        async with ctx.typing():
            await asyncio.sleep(0.5)
        emb = discord.Embed(
            title = 'Command Syntax Error',
            description = f'{ctx.message.author.mention} What do you want me to choose from, blank space <:broo:877044811402735638> !',
            color = ctx.author.color)
        emb.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await ctx.send(embed = emb)

#---emojify---#
    @commands.command(description = 'Send emphasised emoji based texts')
    async def emojify(self,ctx, *, text):
        emojis = []
        for s in text:
            if s.isdecimal():
                num2emo = {'0':'zero','1':'one','2':'two',
                           '3':'three','4':'four','5':'five',
                           '6':'six','7':'seven','8':'eight',
                        '9':'nine'}
                emojis.append(f':{num2emo.get(s)}:')
            elif s.isalpha():
                emojis.append(f':regional_indicator_{s}:')
            else:
                    emojis.append(s)
        async with ctx.typing():
            await asyncio.sleep(0.5)
            await ctx.send(''.join(emojis))
    
    @emojify.error
    async def emojify_error(self, ctx, error):
        async with ctx.typing():
            await asyncio.sleep(0.5)
        await ctx.send(f'{ctx.message.author.mention} Bruh, type something for me to make into an emoji. <:tf:877056779131953173>')
        
#---8 Ball---#
    @commands.command(aliases = ['8ball'], description = 'The Classic 8Ball! Test you luck ')
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
            emb = discord.Embed(
                title = '**Holy Magic 8 Ball**',
                description = f'{ctx.message.author.mention} {random.choice(response)}',
                color = ctx.author.color
            )
            emb.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await asyncio.sleep(0.5)      
        send = await ctx.send(embed = emb)
        await send.add_reaction('🎱')

def setup(bot):
    bot.add_cog(Fun(bot))