from unicodedata import name
import discord
import asyncio

from discord.ext import commands
from discord.enums import ButtonStyle

from Core.Kernel.Utilities.Interface import Confirmation
from Core.Kernel.Utilities.Interface import PAIN
from __main__ import KERNEL

class Developer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # Shuts the bot down in a friendly manner.
    @commands.command(
        name    =   "die", 
        aliases =   ["snap"], 
        brief   =   "Eternal Sleep",
        help    =   "Sends the bot to sleep")
    @commands.is_owner()
    async def die(self, ctx):
        async def YES(UI : discord.ui.View, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
            if INTERACTION.user != ctx.author:
                await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True)
            await UI.response.edit("Okay then, I shall go to eternal sleep", view = None, allowed_mentions = self.bot.Mention)
            UI.stop()
            await self.bot.close()

        async def NO(UI : discord.ui.View, BUTTON: discord.ui.button, INTERACTION : discord.Interaction):
            if INTERACTION.user != ctx.author:
                await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True)
            await UI.response.edit("Seems like I'm gonna be alive for a bit longer",view = None, allowed_mentions = self.bot.Mention)
            UI.stop()
        Confirmation.response    = await ctx.reply("Do you want to kill me?", view = Confirmation(YES, NO), allowed_mentions = self.bot.Mention)
    
    # Loads extension of choice
    @commands.command(
        name    =   "load",
        aliases =   ["l"],
        brief   =   "Loads Cog",
        help    =   "Loads the Extension mentioned.")
    @commands.is_owner()
    async def load(self, ctx, *, COG : str):
        async def YES(UI : discord.ui.View, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
            if INTERACTION.user != ctx.author:
                await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True)
                return
            try:
                self.bot.load_extension(f"Core.Cogs.{COG}")
            except Exception as EXCEPT:
                await UI.response.edit(f"Couldn't load **{COG}** due to : __ {EXCEPT} __ : <:Pain:911261018582306867>", view = None, allowed_mentions = self.bot.Mention)
            else:
                await UI.response.edit(f"loaded : **{COG}** <:RavenPray:914410353155244073>", view = None, allowed_mentions = self.bot.Mention)
            UI.stop()

        async def NO(UI : discord.ui.View, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
            if INTERACTION.user != ctx.author:
                await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True)
                return
            await UI.response.edit(f"Seems like you don't want to load **{COG}**.\nNot my problem <:AkkoHmm:907105376523153458>", view = None, allowed_mentions = self.bot.Mention)
        Confirmation.response    = await ctx.reply(f"Do you want to load : **{COG}** <:Sus:916955986953113630>", view = Confirmation(YES, NO), allowed_mentions = self.bot.Mention)

    # Unloads extension of choice
    @commands.command(
        name    =   "unload",
        aliases =   ["ul"],
        brief   =   "Unloads Cog",
        help    =   "Unloads the Extension mentioned.")
    @commands.is_owner()
    async def unload(self, ctx, *, COG : str):
        async def YES(UI : discord.ui.View, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
            if INTERACTION.user != ctx.author:
                await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True)
                return
            try:
                self.bot.unload_extension(f"Core.Cogs.{COG}")
            except Exception as EXCEPT:
                await UI.response.edit(f"Couldn't unload **{COG}** due to : __ {EXCEPT} __ : <:Pain:911261018582306867>", view = None, allowed_mentions = self.bot.Mention)
            else:
                await UI.response.edit(f"Unloaded : **{COG}** <:RavenPray:914410353155244073>", view = None, allowed_mentions = self.bot.Mention)
            UI.stop()

        async def NO(UI : discord.ui.View, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
            if INTERACTION.user != ctx.author:
                await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True)
                return
            await UI.response.edit(f"Seems like you don't want to unload **{COG}**.\nNot my problem <:AkkoHmm:907105376523153458>", view = None, allowed_mentions = self.bot.Mention)
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
        async def YES(UI : discord.ui.View, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
            if INTERACTION.user != ctx.author:
                await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True)
                return
            try:
                self.bot.reload_extension(f"Core.Cogs.{COG}")
            except Exception as EXCEPT:
                await UI.response.edit(f"Couldn't reload **{COG}** due to : __ {EXCEPT} __ : <:Pain:911261018582306867>", view = None, allowed_mentions = self.bot.Mention)
            else:
                await UI.response.edit(f"Reloaded : **{COG}** <:RavenPray:914410353155244073>", view = None, allowed_mentions = self.bot.Mention)
            UI.stop()

        async def NO(UI : discord.ui.View, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
            if INTERACTION.user != ctx.author:
                await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True)
                return
            await UI.response.edit(f"Seems like you don't want to reload **{COG}**.\nNot my problem <:AkkoHmm:907105376523153458>", view = None, allowed_mentions = self.bot.Mention)
        async with ctx.typing():
            await asyncio.sleep(0.2)
        Confirmation.response    = await ctx.reply(f"Do you want to reload : **{COG}** <:Sus:916955986953113630>", view = Confirmation(YES, NO), allowed_mentions = self.bot.Mention)

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
            status  =   discord.Status.invisible)
        await ctx.message.add_reaction("<:Offline:905757032521551892>")
    
    @dev.command(
        name    =   "off",
        brief   =   "Sets Status Idle",
        help    =   "Sets the bot status as Idle")
    async def off(self, ctx):
        await self.bot.change_presence(
            status  =   discord.Status.idle,
            activity    =   discord.Activity(type = discord.ActivityType.listening, name = ".ghelp"))
        await ctx.message.add_reaction("<:Idle:905757063064453130>")
    
def setup(bot):
    bot.add_cog(Developer(bot))