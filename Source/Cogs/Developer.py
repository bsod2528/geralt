import io
import disnake
import asyncio
import textwrap
import traceback
import contextlib

from disnake.ext import commands
from disnake.enums import ButtonStyle

from __main__ import KERNEL
from Source.Kernel.Views.Interface import Confirmation, PAIN

# Sub - Class for buttons in eval command.
class EvalButtons(disnake.ui.View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx    =   ctx
    
    @disnake.ui.button(label = "Traceback", style = ButtonStyle.gray)
    async def TRACEBACK(self, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction):
        TB_EMB  =   disnake.Embed(
            title   =   "Errors Going Boing",
            description =   f"{Exception.__class__.__name__} -> {Exception}",
            colour  =   self.bot.colour)
        await INTERACTION.response.send_message(embed = TB_EMB, ephemeral = True)

class Developer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # Shuts the bot down in a friendly manner.
    @commands.command(
        name    =   "die", 
        aliases =   ["snap"], 
        brief   =   "Eternal Sleep",
        help    =   "Sends the bot to eternal sleep")
    @commands.is_owner()
    async def die(self, ctx):
        async def YES(UI : disnake.ui.View, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction):
            if INTERACTION.user != ctx.author:
                await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True)
            await UI.response.edit(content = "Okay then, I shall go to eternal sleep", view = None, allowed_mentions = self.bot.Mention)
            UI.stop()
            await self.bot.close()

        async def NO(UI : disnake.ui.View, BUTTON: disnake.ui.button, INTERACTION : disnake.Interaction):
            if INTERACTION.user != ctx.author:
                await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True)
            await UI.response.edit(content = "Seems like I'm gonna be alive for a bit longer",view = None, allowed_mentions = self.bot.Mention)
            UI.stop()
        Confirmation.response    = await ctx.reply("Do you want to kill me?", view = Confirmation(YES, NO), allowed_mentions = self.bot.Mention)
    
    # Evaluate command for running both asynchronous and sychronous programs.
    @commands.command(
        name    =   "eval",
        aliases =   ["e"],
        brief   =   "Run Code",
        help    =   "Running both asynchronous and sychronous programs")
    @commands.is_owner()
    async def eval(self, ctx, *, body : str):
        env = {
            'self'      :   self,
            'disnake'   :   disnake,
            'bot'       :   self.bot,
            'ctx'       :   ctx,
            'message'   :   ctx.message,
            'author'    :   ctx.author,
            'guild'     :   ctx.guild,
            'channel'   :   ctx.channel,
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
            emb = disnake.Embed(
                description = f'```py\n{e.__class__.__name__} --> {e}\n```',
                colour = self.bot.colour)
            return await ctx.send(embed = emb)
        func = env["func"]
        try:
            with contextlib.redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            emb = disnake.Embed(
                description = f'```py\n{value}{traceback.format_exc()}\n```',
                color = 0x2F3136)
            message = await ctx.send(embed = emb)
            await ctx.message.add_reaction('<:WinUnheck:898572376147623956>')
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction('<:WinCheck:898572324490604605>')
            except:
                pass
            if ret is None:
                if value:
                    emb = disnake.Embed(
                        description = f'```py\n{value}\n```',
                        colour = self.bot.colour)
                    await ctx.send(embed = emb, mention_author = False)
            else:
                emb = disnake.Embed(
                    description = f'```py\n{value}{ret}\n```',
                    colour = self.bot.colour)
                await ctx.send(embed = emb, mention_author = False)

    # Loads extension of choice
    @commands.command(
        name    =   "load",
        aliases =   ["l"],
        brief   =   "Loads Cog",
        help    =   "Loads the Extension mentioned.")
    @commands.is_owner()
    async def load(self, ctx, *, COG : str):
        async def YES(UI : disnake.ui.View, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction):
            if INTERACTION.user != ctx.author:
                await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True)
                return
            try:
                self.bot.load_extension(f"Source.Cogs.{COG}")
            except Exception as EXCEPT:
                await UI.response.edit(content = f"Couldn't load **{COG}** due to : __ {EXCEPT} __ : <:Pain:911261018582306867>", view = None, allowed_mentions = self.bot.Mention)
            else:
                await UI.response.edit(content = f"Loaded : **{COG}** <:RavenPray:914410353155244073>", view = None, allowed_mentions = self.bot.Mention)
            UI.stop()

        async def NO(UI : disnake.ui.View, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction):
            if INTERACTION.user != ctx.author:
                await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True)
                return
            await UI.response.edit(content = f"Seems like you don't want to load **{COG}**.\nNot my problem <:AkkoHmm:907105376523153458>", view = None, allowed_mentions = self.bot.Mention)
        Confirmation.response    = await ctx.reply(f"Do you want to load : **{COG}** <:Sus:916955986953113630>", view = Confirmation(YES, NO), allowed_mentions = self.bot.Mention)

    # Unloads extension of choice
    @commands.command(
        name    =   "unload",
        aliases =   ["ul"],
        brief   =   "Unloads Cog",
        help    =   "Unloads the Extension mentioned.")
    @commands.is_owner()
    async def unload(self, ctx, *, COG : str):
        async def YES(UI : disnake.ui.View, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction):
            if INTERACTION.user != ctx.author:
                await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True)
                return
            try:
                self.bot.unload_extension(f"Source.Cogs.{COG}")
            except Exception as EXCEPT:
                await UI.response.edit(content = f"Couldn't unload **{COG}** due to : __ {EXCEPT} __ : <:Pain:911261018582306867>", view = None, allowed_mentions = self.bot.Mention)
            else:
                await UI.response.edit(content = f"Unloaded : **{COG}** <:RavenPray:914410353155244073>", view = None, allowed_mentions = self.bot.Mention)
            UI.stop()

        async def NO(UI : disnake.ui.View, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction):
            if INTERACTION.user != ctx.author:
                await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True)
                return
            await UI.response.edit(content = f"Seems like you don't want to unload **{COG}**.\nNot my problem <:AkkoHmm:907105376523153458>", view = None, allowed_mentions = self.bot.Mention)
        async with ctx.typing():
            await asyncio.sleep(0.2)
        Confirmation.response    = await ctx.reply(f"Do you want to unload : **{COG}** <:Sus:916955986953113630>", view = Confirmation(YES, NO), allowed_mentions = self.bot.Mention)
    
    # Reloads extension of choice
    @commands.command(
        name    =   "reload",
        aliases =   ["rl"],
        brief   =   "Reloads Cog",
        help    =   "Reloads the Extension mentioned.")
    @commands.is_owner()
    async def reload(self, ctx, *, COG : str):
        try:
            self.bot.reload_extension(f"Source.Cogs.{COG}")
            await ctx.reply(f"**{COG}** : Successfully Reloaded <:RavenPray:914410353155244073>", allowed_mentions = self.bot.Mention)
        except Exception as EXCEPT:
            await ctx.reply(f"Couldn't reload **{COG}** : `{EXCEPT}`", allowed_mentions = self.bot.Mention)
    # Group of Commands used for changing presence and toggling no prefix
    @commands.group(
        name    =   "dev",
        aliases =   ["devmode"],
        brief   =   "Simple Dev Stuff",
        help    =   "Simple commands for dev to do")
    @commands.is_owner()
    async def dev(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @dev.command(
        name    =   "on",
        brief   =   "Sets Status Offline",
        help    =   "Sets the bot status as Invisible")
    async def on(self, ctx):
        await self.bot.change_presence(
            status  =   disnake.Status.invisible)
        await ctx.message.add_reaction("<:Offline:905757032521551892>")
    
    @dev.command(
        name    =   "off",
        brief   =   "Sets Status Idle",
        help    =   "Sets the bot status as Idle")
    async def off(self, ctx):
        await self.bot.change_presence(
            status  =   disnake.Status.idle,
            activity    =   disnake.Activity(type = disnake.ActivityType.listening, name = ".ghelp"))
        await ctx.message.add_reaction("<:Idle:905757063064453130>")
    
def setup(bot):
    bot.add_cog(Developer(bot))