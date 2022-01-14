import discord
import asyncio

from discord.ext import commands
from discord.enums import ButtonStyle

from Kernel.Utilities.Interface import Confirmation
from Kernel.Utilities.Interface import PAIN

class Developer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
   
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
                self.bot.load_extension(f"Cogs.{COG}")
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
                self.bot.unload_extension(f"Cogs.{COG}")
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
                self.bot.reload_extension(f"Cogs.{COG}")
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

    @commands.command()
    async def test(self, ctx):
        time = self.bot.Timestamp
        await ctx.send(f"{discord.utils.format_dt(time, style = 'D')}")


def setup(bot):
    bot.add_cog(Developer(bot))