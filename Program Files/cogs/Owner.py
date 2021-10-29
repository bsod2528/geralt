import os
import sys
import asyncio
import discord
import datetime
import logging
import json
import random
import asyncpg
import contextlib
import traceback
import io
import textwrap
from discord.ui import view
import Kernel.Utils.Buttons as Button
from discord import user, channel
from discord.enums import InteractionType
from discord.ext import commands
from discord.ext.commands import bot, converter
from discord.ext.commands.core import command, is_owner
from discord.interactions import Interaction
from logging import exception

class AV(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.color = discord.Color.from_rgb(117, 128, 219)
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)
        self.json = json.load(open('Program Files\Emotes.json'))
        super().__init__()

    def av(ctx):
        return ctx.author.id == 750979369001811982 , 760823877034573864, 778251218505433098

    @commands.command(
        name = 'unload', 
        help = f'```ini\n[ Syntax : .gunload cogs.<cog name> ]\n```\n>>> __***Bot Owner command, dont even think about running this <:AkkoThink:898611207995543613>***__\n**USE :** Unload Cogs in a fraction of a second!\n**AKA :** No aliases present ;)', 
        brief = 'Unload dem!')
    @commands.is_owner()
    async def unload(self, ctx, *, cog : str):
        emote = self.json
        try:

            self.bot.unload_extension(cog)
        except Exception as e:
            await ctx.reply(f'{emote["Win"]["critical"]} {type(e).__name__} - {e}')
        else:
            unload  =   [f'Please wait, unloading cog set to happen in background {emote["Girl"]["okay"]}',
                        f'Cog is being unloaded, please wait {emote["Girl"]["laugh"]}',
                        f'Your selection of cog is being unloaded mate {emote["Girl"]["laugh"]}',
                        f'{emote["Girl"]["okay"]}']
            async with ctx.typing():
                await asyncio.sleep(0.5)
            message = await ctx.reply(f'{random.choice(unload)}')
            await asyncio.sleep(2)
            await message.edit(f'{emote["Win"]["check"]} Cog Unloaded ')
    

    @commands.command(
        name = 'load', 
        help = f'```ini\n[ Syntax : .gload cogs.<cog name> ]\n```\n>>> __***Bot Owner command, dont even think about running this <:AkkoThink:898611207995543613>***__\n**USE :** Load Cogs faster than Mcqueen!\n**AKA :** No aliases present ;)', 
        brief = 'Load em')
    @commands.is_owner()
    async def load(self, ctx, *, cog : str):
        emote = self.json
        try:
            self.bot.load_extension(cog)
        except Exception as e:
            await ctx.replyt(f'{emote["Win"]["critical"]} {type(e).__name__} - {e}')
        else:
            load    =   [f'Just a second, I am loading the cog {emote["Girl"]["laugh"]}',
                        f'Cog being loaded, please wait {emote["Girl"]["okay"]}',
                        f'The cog of your choice is being loaded {emote["Girl"]["okay"]}']
            async with ctx.typing():
                await asyncio.sleep(0.5)
            message = await ctx.reply(f'{random.choice(load)}')
            await asyncio.sleep(2)
            await message.edit(f'{emote["Win"]["check"]} Cog Loaded ')
    
    @commands.command(
        name = 'reload',
        help = f'```ini\n[ Syntax : .greload cogs.<cog name>]\n```\n>>> __***Bot Owner command, dont even think about running this <:AkkoThink:898611207995543613>***__\n**USE :** Reloads cogs for...nvm\n**AKA :** No aliases present ;')
    @commands.is_owner()
    async def reload(self, ctx, *, cog : str):
        emote = self.json
        try:
            self.bot.reload_extension(cog)
        except Exception as e:
            async with ctx.typing():
                await asyncio.sleep(0.5)
            await ctx.reply(f'{emote["Win"]["critical"]} {type(e).__name__} - {e}')
        else:
            reload  =   [f'Reloading Cog {emote["Girl"]["okay"]}',
                        f'The cog is being reloaded, please wait {emote["Girl"]["okay"]}',
                        f'BOOM {emote["Girl"]["okay"]}']
            async with ctx.typing():
                await asyncio.sleep(0.5)
            message = await ctx.reply(f'{random.choice(reload)}')
            await asyncio.sleep(2)
            await message.edit(f'{emote["Win"]["check"]} Cog reloaded succesfully')
        
    @commands.command(
        name = 'loadjsk', 
        help = f'```ini\n[ Syntax : .gloadjsk ]\n```\n>>> __***Bot Owner command, dont even think about running this <:AkkoThink:898611207995543613>***__\n**USE :** Loads Jishaku as a COG\n**AKA :** No aliases present ;)')
    @commands.is_owner()
    async def loadjsk(self, ctx):
        emote = self.json
        async with ctx.typing():
            self.bot.load_extension('jishaku')
            await asyncio.sleep(0.5)
        await ctx.reply(f'Done! JISHAKU now loaded up for... Well for running the commands you dumbo')

    @commands.command(
        name = 'die',
        aliases = ['snap'],
        help = f'```ini\n[ Syntax : .gdie ]\n```\n>>> __***Bot Owner command, dont even think about running this <:AkkoThink:898611207995543613>***__\n**USE :** If my dev uses it, I Die\n**AKA :** `.gsnap`',
        brief = 'kills da bot')
    @commands.is_owner()
    async def die(self, ctx):
        emote = self.json
        await ctx.reply(f'Are you sure about what you just chose now?', view = Button.Die(bot = self.bot))

    @commands.command(
        name="toggle", 
        help = f'```ini\n[ Syntax : .gtoggle <command name> ]\n```\n>>> __***Bot Owner command, dont even think about running this <:AkkoThink:898611207995543613>***__\n**USE :** Enable or disable a command!\n**AKA :** `.gtog`', 
        aliases = ['tog'])
    @commands.is_owner()
    async def toggle(self, ctx, *, command):
        emote = self.json
        command = self.bot.get_command(command)

        if command is None:
            async with ctx.typing():
                await asyncio.sleep(0.5)
            await ctx.reply(f'{emote["frog"]["worryrun"]} I cant find a command with that name!')

        elif ctx.command == command:
            async with ctx.typing():
                await asyncio.sleep(0.5)
            await ctx.reply(f'{emote["anxiety"]["trigger"]}You cannot disable this command')

        else:
            command.enabled = not command.enabled
            cmdstat = "enabled" if command.enabled else "disabled"
            async with ctx.typing():
                await asyncio.sleep(0.5)
            await ctx.reply(f'I have {cmdstat} {command.qualified_name} for you! {emote["peep"]["prayage"]}',)

    @commands.command(
        name = 'eval',
        aliases = ['e'],
        help = f'```ini\n[ Syntax : .geval <code here> ]\n```\n>>> __***Bot Owner command, dont even think about running this <:AkkoThink:898611207995543613>***__\n**USE :** Evalutes the code given by BSOD\n**AKA :** `.ge`')
    @commands.is_owner()
    async def eval(self, ctx, *, body:str):
        env = {
            "self": self,
            "discord": discord,
            "bot": self.bot,
            "ctx": ctx,
            "message": ctx.message,
            "author": ctx.author,
            "guild": ctx.guild,
            "channel": ctx.channel,
        }
        env.update(globals())
        if body.startswith( '```' ) and body.endswith( '```' ):
            body = '\n'.join(body.split('\n')[1:-1])
        body = body.strip('` \n')
        stdout = io.StringIO()
        to_compile = F"async def func():\n{textwrap.indent(body, '  ')}"
        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.reply(f'```py\n{e.__class__.__name__} --> {e}\n```', view = Button.ExceptionButton())
        func = env["func"]
        try:
            with contextlib.redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```', view = Button.ExceptionButton())
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction('<:WinCheck:898572324490604605>')
            except:
                pass
            if ret is None:
                if value:
                    await ctx.reply(f'```py\n{value}\n```')
            else:
                await ctx.reply(f'```py\n{value}{ret}\n```')

def setup(bot):
    bot.add_cog(AV(bot))