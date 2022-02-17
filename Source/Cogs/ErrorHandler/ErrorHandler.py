import io
import os
import aiohttp
import disnake
import traceback

from disnake.ext import commands
from disnake.enums import ButtonStyle
from disnake.webhook.async_ import Webhook

from __main__ import KERNEL, SESSION_CREATE
import Source.Kernel.Views.Interface as Interface

class ErrorHandler(commands.Cog):
    """Global Error Handling"""
    def __init__(self, bot):
        self.bot        =   bot        
        self.session    =   aiohttp.ClientSession()
        self.webhook    =   Webhook.from_url(os.getenv("ERROR"), session = self.session)
        self.Footer     =   "Click on the buttons for info."        
        
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):

        if hasattr(ctx.command, "on_error"):
            return

        error   =   getattr(error, "original", error)
            
        if isinstance(error, commands.CommandNotFound):
            return
        
        if isinstance(error, commands.DisabledCommand):
            DISABLED_EMB    =   disnake.Embed(
                title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {ctx.command}",
                description = f"```prolog\n {error} \n```<:Reply:930634822865547294> **Occurance :** {self.bot.DT(ctx.message.created_at, style = 'F')}",
                colour = 0x2F3136)
            DISABLED_EMB.set_footer(text = self.Footer)
            await ctx.trigger_typing()
            return await ctx.reply(embed = DISABLED_EMB, mention_author = False, view = Interface.Traceback(ctx, error))
    
        if  isinstance(error, commands.BotMissingPermissions):
            BOT_MISSING_PERMS_EMB   =   disnake.Embed(
                title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {ctx.command}",
                description = f"```prolog\n {error} \n```\n<:Reply:930634822865547294> **Occurance :** {self.bot.DT(ctx.message.created_at, style = 'F')}",
                colour = 0x2F3136)
            BOT_MISSING_PERMS_EMB.set_footer(text = self.Footer)
            await ctx.trigger_typing()
            return await ctx.reply(embed = BOT_MISSING_PERMS_EMB, mention_author = False, view = Interface.Traceback(ctx, error))
        
        if isinstance(error, commands.MissingPermissions):
            MISSING_PERMS_EMB   =   disnake.Embed(
                title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {ctx.command}",
                description = f"```prolog\n {error} \n```\n<:Reply:930634822865547294> **Occurance :** {self.bot.DT(ctx.message.created_at, style = 'F')}",
                colour = 0x2F3136)
            MISSING_PERMS_EMB.set_footer(text = self.Footer)
            await ctx.trigger_typing()
            return await ctx.reply(embed = MISSING_PERMS_EMB, mention_author = False, view = Interface.Traceback(ctx, error))

        if isinstance(error, commands.NotOwner):
            return
        
        if isinstance(error, commands.MissingRequiredArgument):
            ARGS_MISSING_EMB    =   disnake.Embed(
                title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {ctx.command}",
                description = f"```prolog\n {error} \n```\nClick on the `Syntax` Button for the proper syntax of `{ctx.command}`\n\n<:Reply:930634822865547294> **Occurance :** {self.bot.DT(ctx.message.created_at, style = 'F')}",
                colour = 0x2F3136)
            ARGS_MISSING_EMB.set_footer(text = self.Footer)
            await ctx.trigger_typing()
            return await ctx.reply(embed = ARGS_MISSING_EMB, mention_author = False, view = Interface.CommandSyntax(ctx, error))
        
        if isinstance(error, commands.MemberNotFound):
            MEMBER_MISSING_EMB    =   disnake.Embed(
                title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {ctx.command}",
                description = f"```prolog\n {error} \n```\n<:Reply:930634822865547294> **Occurance :** {self.bot.DT(ctx.message.created_at, style = 'F')}",
                colour = 0x2F3136)
            MEMBER_MISSING_EMB.set_footer(text = self.Footer)
            await ctx.trigger_typing()
            return await ctx.reply(embed = MEMBER_MISSING_EMB, mention_author = False, view = Interface.Traceback(ctx, error))

        if isinstance(error, commands.BadArgument):
            BAD_ARGS_EMB    =   disnake.Embed(
                title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {ctx.command}",
                description = f"```prolog\n {error} \n```\n<:Reply:930634822865547294> **Occurance :** {self.bot.DT(ctx.message.created_at, style = 'F')}",
                colour = 0x2F3136)    
            BAD_ARGS_EMB.set_footer(text = self.Footer)
            await ctx.trigger_typing()
            return await ctx.reply(embed = BAD_ARGS_EMB,mention_author = False, view = Interface.Traceback(ctx, error))

        if isinstance(error, commands.errors.CommandOnCooldown):
            COOLDOWN_EMB    =   disnake.Embed(
                title = f"<:GeraltRightArrow:904740634982760459> COMMAND ERRORED : {ctx.command}",
                description = f"```prolog\n {error} \n```\n<:Reply:930634822865547294> **Occurance :** {self.bot.DT(ctx.message.created_at, style = 'F')}",
                colour = 0x2F3136)
            COOLDOWN_EMB.set_footer(text = self.Footer)
            await ctx.trigger_typing()
            return await ctx.reply(embed = COOLDOWN_EMB,mention_author = False, view = Interface.Traceback(ctx, error))

        else:
            if ctx.guild:
                command_data    =   f"- Occured By    :   {ctx.author} / {ctx.author.id}\n" \
                                    f"- Command Name  :   {ctx.message.content}\n" \
                                    f"- @ Guild       :   {ctx.guild} / {ctx.guild.id}\n" \
                                    f"- @ Channel     :   {ctx.channel} / {ctx.channel.id}"
            else:
                command_data    =   f"- Occured By    :   {ctx.author} /{ctx.author.id}\n" \
                                    f"- Command Name  :   {ctx.message.content}\n" \
                                    f"** Occured in DM's **"
            error_str   =   "".join(traceback.format_exception(type(error), error, error.__traceback__))
            error_emb   =   disnake.Embed(
                title = "Error Boi <:Pain:911261018582306867>",
                description = f"```prolog\n{command_data} \n```\n```py\n {error_str}\n```",
                colour = 0x2F3136)       
            error_emb.timestamp = disnake.utils.utcnow()           
            send_error  =   self.webhook
            if len(error_str) < 2000:
                try:
                    await send_error.send(embed = error_emb)
                    await send_error.send("||Break Point||")
                except(disnake.HTTPException, disnake.Forbidden):
                    await send_error.send(embed = error_emb, file = disnake.File(io.StringIO(error_str), filename = "Traceback.py"))
                    await send_error.send("||Break Point||")
            else:
                await send_error.send(embed = error_emb, file = disnake.File(io.StringIO(error_str), filename = "Traceback.py"))
                await send_error.send("||Break Point||")
        
def setup(bot):
    bot.add_cog(ErrorHandler(bot))