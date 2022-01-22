import io
import json
import aiohttp
import disnake
import datetime
import traceback

from disnake.ext import commands
from disnake.enums import ButtonStyle
from disnake.webhook.async_ import Webhook

from __main__ import KERNEL
from Source.Kernel.Views.Interface import PAIN


class ErrorView(disnake.ui.View):
    def __init__(self, ctx, ERROR):
        super().__init__()
        self.ctx    =   ctx
        self.ERROR  =   ERROR

    @disnake.ui.button(label = "Traceback", style = ButtonStyle.blurple, emoji = "<:WinTerminal:898609124982554635>")
    async def Error(self, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction):
        ERROR   =   getattr(self.ERROR, "original", self.ERROR)
        ERROR_EMB   =   disnake.Embed(
            title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {self.ctx.command}",
            description = f"```yaml\n Quick Tip : Read the last 2 - 3 lines for proper info.\n```\n```py\n {''.join(traceback.format_exception(type(ERROR), ERROR, ERROR.__traceback__))}\n```\n",   
            colour = 0x2F3136)
        await INTERACTION.response.send_message(embed = ERROR_EMB, ephemeral = True)    
    
    @disnake.ui.button(label = "Delete", style = ButtonStyle.blurple, emoji = "<a:Trash:906004182463569961>")
    async def Delete(self, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction):
        await INTERACTION.response.send_message("Deleting the message as you wish", ephemeral = True)
        await INTERACTION.message.delete()

    async def interaction_check(self, INTERACTION : disnake.Interaction) -> bool:
            if INTERACTION.user == self.ctx.author:
                return True
            await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True)

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot        =   bot        
        self.session    =   aiohttp.ClientSession()
        self.WEBHOOK    =   Webhook.from_url(KERNEL["Tokens"]["Error"], session = self.session)
        self.TS         =   disnake.utils.format_dt(datetime.datetime.now(datetime.timezone.utc), style = "F")
        self.Footer     =   "Please click on the Traceback button for proper information on where you have gone wrong :D"        
        
    @commands.Cog.listener()
    async def on_command_error(self, ctx, ERROR):
        ERROR   =   getattr(ERROR, "original", ERROR)
        
        if isinstance(ERROR, commands.CommandNotFound):
            return
        
        if isinstance(ERROR, commands.DisabledCommand):
            DISABLED_EMB    =   disnake.Embed(
                title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {ctx.command}",
                description = f"```py\n {ERROR} \n```<:Reply:930634822865547294> **Occurance :** {self.TS}",
                colour = 0x2F3136)
            DISABLED_EMB.set_footer(text = self.Footer)
            await ctx.trigger_typing()
            await ctx.reply(embed = DISABLED_EMB, mention_author = False, view = ErrorView(ctx, ERROR))
    
        if  isinstance(ERROR, commands.BotMissingPermissions):
            BOT_MISSING_PERMS_EMB   =   disnake.Embed(
                title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {ctx.command}",
                description = f"```py\n {ERROR} \n```\n<:Reply:930634822865547294> **Occurance :** {self.TS}",
                colour = 0x2F3136)
            BOT_MISSING_PERMS_EMB.set_footer(text = self.Footer)
            await ctx.trigger_typing()
            await ctx.reply(embed = BOT_MISSING_PERMS_EMB, mention_author = False, view = ErrorView(ctx, ERROR))
        
        if isinstance(ERROR, commands.MissingPermissions):
            MISSING_PERMS_EMB   =   disnake.Embed(
                title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {ctx.command}",
                description = f"```py\n {ERROR} \n```\n<:Reply:930634822865547294> **Occurance :** {self.TS}",
                colour = 0x2F3136)
            MISSING_PERMS_EMB.set_footer(text = self.Footer)
            await ctx.trigger_typing()
            await ctx.reply(embed = MISSING_PERMS_EMB, mention_author = False, view = ErrorView(ctx, ERROR))

        if isinstance(ERROR, commands.NotOwner):
            pass
        
        if isinstance(ERROR, commands.MissingRequiredArgument):
            ARGS_MISSING_EMB    =   disnake.Embed(
                title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {ctx.command}",
                description = f"```py\n {ERROR} \n```\n<:Reply:930634822865547294> **Occurance :** {self.TS}",
                colour = 0x2F3136)
            ARGS_MISSING_EMB.set_footer(text = self.Footer)
            await ctx.trigger_typing()
            await ctx.reply(embed = ARGS_MISSING_EMB, mention_author = False, view = ErrorView(ctx, ERROR))
        
        if isinstance(ERROR, commands.BadArgument):
            BAD_ARGS_EMB    =   disnake.Embed(
                title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {ctx.command}",
                description = f"```py\n {ERROR} \n```\n<:Reply:930634822865547294> **Occurance :** {self.TS}",
                colour = 0x2F3136)    
            BAD_ARGS_EMB.set_footer(text = self.Footer)
            await ctx.reply(embed = BAD_ARGS_EMB,mention_author = False, view = ErrorView(ctx, ERROR)   )

        if isinstance(ERROR, commands.errors.CommandOnCooldown):
            COOLDOWN_EMB    =   disnake.Embed(
                title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {ctx.command}",
                description = f"```py\n {ERROR} \n```\n<:Reply:930634822865547294> **Occurance :** {self.TS}",
                colour = 0x2F3136)
            COOLDOWN_EMB.set_footer(text = self.Footer)
            await ctx.trigger_typing()
            await ctx.reply(embed = COOLDOWN_EMB,mention_author = False, view = ErrorView(ctx, ERROR))

        else:
            if ctx.guild:
                COMMAND_DATA    =   f"- Occured By    :   {ctx.author} / {ctx.author.id}\n" \
                                    f"- Command Name  :   {ctx.message.content}\n" \
                                    f"- @ Guild       :   {ctx.guild} / {ctx.guild.id}\n" \
                                    f"- @ Channel     :   {ctx.channel} / {ctx.channel.id}"
            else:
                COMMAND_DATA    =   f"- Occured By    :   {ctx.author} /{ctx.author.id}\n" \
                                    f"- Command Name  :   {ctx.message.content}\n" \
                                    f"** Occured in DM's **"
            ERROR_STR   =   "".join(traceback.format_exception(type(ERROR), ERROR, ERROR.__traceback__))
            ERROR_EMB   =   disnake.Embed(
                title = "Error Boi <:Pain:911261018582306867>",
                description = f"```yaml\n{COMMAND_DATA} \n```\n```py\n {ERROR_STR}\n```",
                colour = 0x2F3136)       
            ERROR_EMB.timestamp = self.bot.Timestamp                     
            SEND_ERROR  =   self.WEBHOOK
            if len(ERROR_STR) < 2000:
                try:
                    await SEND_ERROR.send(embed = ERROR_EMB)
                    await SEND_ERROR.send("||Break Point||")
                except(disnake.HTTPException, disnake.Forbidden):
                    await SEND_ERROR.send(embed = ERROR_EMB, file = disnake.File(io.StringIO(ERROR_STR), filename = "Traceback.py"))
                    await SEND_ERROR.send("||Break Point||")
            else:
                await SEND_ERROR.send(embed = ERROR_EMB, file = disnake.File(io.StringIO(ERROR_STR), filename = "Traceback.py"))
                await SEND_ERROR.send("||Break Point||")

def setup(bot):
    bot.add_cog(ErrorHandler(bot))