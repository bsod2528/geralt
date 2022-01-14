import sys
import aiohttp
import discord
import datetime
import traceback

from discord.ext import commands
from discord.enums import ButtonStyle
from discord.webhook.async_ import Webhook

from __main__ import KERNEL
from Kernel.Utilities.Interface import PAIN

class ErrorView(discord.ui.View):
    def __init__(self, ctx, ERROR):
        super().__init__()
        self.ctx    =   ctx
        self.ERROR  =   ERROR

    @discord.ui.button(label = "Traceback", style = ButtonStyle.blurple, emoji = "<:WinTerminal:898609124982554635>")
    async def Error(self, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
        ERROR   =   getattr(self.ERROR, "original", self.ERROR)
        ERROR_EMB   =   discord.Embed(
            title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {self.ctx.command}",
            description = f"```yaml\n Best Tip : Read the last 2 - 3 lines for proper info.\n```\n```py\n {traceback.format_exception(type(ERROR), ERROR, ERROR.__traceback__)} \n```\n",   
            colour = 0x2F3136)
        await INTERACTION.response.send_message(embed = ERROR_EMB, ephemeral = True)
          
    async def interaction_check(self, INTERACTION : discord.Interaction) -> bool:
        if INTERACTION.user == self.ctx.author:
            return True
        await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True)
    
    @discord.ui.button(label = "Delete", style = ButtonStyle.blurple, emoji = "<a:Trash:906004182463569961>")
    async def Delete(self, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
        await INTERACTION.response.send_message("Deleting the message as you wish", ephemeral = True)
        await INTERACTION.message.delete()

    async def interaction_check(self, INTERACTION : discord.Interaction) -> bool:
            if INTERACTION.user == self.ctx.author:
                return True
            await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True)

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot    = bot
        self.Footer = "Please click on the Traceback button for proper information on where you have gone wrong :D"
        self.TS     = discord.utils.format_dt(datetime.datetime.now(datetime.timezone.utc), style = "F")
        
    @commands.Cog.listener()
    async def on_command_error(self, ctx, ERROR):
        ERROR   =   getattr(ERROR, "original", ERROR)
        
        if isinstance(ERROR, commands.DisabledCommand):
            DISABLED_EMB    =   discord.Embed(
                title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {ctx.command}",
                description = f"```py\n {ERROR} \n```<:Reply:930634822865547294> **Occurance :** __ {self.TS} __",
                colour = 0x2F3136)
            DISABLED_EMB.set_footer(text = self.Footer)
            await ctx.trigger_typing()
            await ctx.reply(embed = DISABLED_EMB, mention_author = False, view = ErrorView(ctx, ERROR))
    
        if  isinstance(ERROR, commands.BotMissingPermissions):
            BOT_MISSING_PERMS_EMB   =   discord.Embed(
                title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {ctx.command}",
                description = f"```py\n {ERROR} \n```\n<:Reply:930634822865547294> **Occurance :**{self.TS}",
                colour = 0x2F3136)
            BOT_MISSING_PERMS_EMB.set_footer(text = self.Footer)
            await ctx.trigger_typing()
            await ctx.reply(embed = BOT_MISSING_PERMS_EMB, mention_author = False, view = ErrorView(ctx, ERROR))
        
        if isinstance(ERROR, commands.MissingPermissions):
            MISSING_PERMS_EMB   =   discord.Embed(
                title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {ctx.command}",
                description = f"```py\n {ERROR} \n```\n<:Reply:930634822865547294> **Occurance :**{self.TS}",
                colour = 0x2F3136)
            MISSING_PERMS_EMB.set_footer(text = self.Footer)
            await ctx.trigger_typing()
            await ctx.reply(embed = MISSING_PERMS_EMB, mention_author = False, view = ErrorView(ctx, ERROR))

        if isinstance(ERROR, commands.NotOwner):
            NOT_OWNER_EMB   =   discord.Embed(
                title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {ctx.command}",
                description = f"```py\n {ERROR} \n```\n<:Reply:930634822865547294> **Occurance :**{self.TS}",
                colour = 0x2F3136)
            NOT_OWNER_EMB.set_footer(text = self.Footer)
            await ctx.trigger_typing()
            await ctx.reply(embed = NOT_OWNER_EMB, mention_author = False, view = ErrorView(ctx, ERROR))
        
        if isinstance(ERROR, commands.MissingRequiredArgument):
            ARGS_MISSING_EMB    =   discord.Embed(
                title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {ctx.command}",
                description = f"```py\n {ERROR} \n```\n<:Reply:930634822865547294> **Occurance :**{self.TS}",
                colour = 0x2F3136)
            ARGS_MISSING_EMB.set_footer(text = self.Footer)
            await ctx.trigger_typing()
            await ctx.reply(embed = ARGS_MISSING_EMB, mention_author = False, view = ErrorView(ctx, ERROR))
        
        if isinstance(ERROR, commands.BadArgument):
            BAD_ARGS_EMB    =   discord.Embed(
                title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {ctx.command}",
                description = f"```py\n {ERROR} \n```\n<:Reply:930634822865547294> **Occurance :**{self.TS}",
                colour = 0x2F3136)    
            BAD_ARGS_EMB.set_footer(text = self.Footer)
            await ctx.reply(embed = BAD_ARGS_EMB,mention_author = False, view = ErrorView(ctx, ERROR)   )

        if isinstance(ERROR, commands.errors.CommandOnCooldown):
            COOLDOWN_EMB    =   discord.Embed(
                title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {ctx.command}",
                description = f"This command is currently cooldown. Please wait for a few seconds in order to invoke it again.\n\n<:Reply:930634822865547294> **Occurance :**{self.TS}",
                colour = 0x2F3136)
            COOLDOWN_EMB.set_footer(text = self.Footer)
            await ctx.trigger_typing()
            await ctx.reply(embed = COOLDOWN_EMB,mention_author = False, view = ErrorView(ctx, ERROR))

        else:
            async def LOG_ERROR(self, ctx, ERROR):
                self.session    =   aiohttp.ClientSession()
                self.WEBHOOK  =   Webhook.from_url(KERNEL["Tokens"]["ErrorWBHK"], session = self.session)
                LOG_ERROR_EMB   =   discord.Embed(
                    title = "Error goes Boing",
                    description = f"{ctx.message.content}",
                    colour = 0x2F3136)
                LOG_ERROR_EMB.add_field(
                    name = "Person Invoked It :",
                    value = f"**Name :** {ctx.author.mention} | `{ctx.author.id}`")
                LOG_ERROR_EMB.add_field(
                    name = "Command Invoked At :",
                    value = f"**<:ReplyContinued:930634770004725821> Guild :** `{ctx.guild.name}` | `{ctx.guild.id}`\n**<:Reply:930634822865547294> Channel :** <#{ctx.channel.id}> | `{ctx.channel.id}`")
                LOG_ERROR_EMB.add_field(
                    name = "General :",
                    value = f"**<:ReplyContinued:930634770004725821> Occurance :** {self.TS}\n**<:Reply:930634822865547294> Message URL :** [**Click Here**]({ctx.message.jump_url})")
        
                FULL_TRACEBACK = ''.join(traceback.format_exception(type(ERROR), ERROR, ERROR.__traceback__))
                
                First_Half, Second_Half = "", []
                
                for LINE in FULL_TRACEBACK.split('\n'):
                    if len(First_Half + LINE) < 1900:
                        First_Half += f"\n{LINE}"
                    else:
                        Second_Half.append(First_Half)
                        First_Half = ""
                        Second_Half.append(First_Half)

                LOG_ERROR = self.WEBHOOK
                await self.WEBHOOK.send(embed = LOG_ERROR_EMB)   
                for EXCEPTION in Second_Half:
                    await LOG_ERROR.send(f"```py\n {EXCEPTION} \n```")

def setup(bot):
    bot.add_cog(ErrorHandler(bot))