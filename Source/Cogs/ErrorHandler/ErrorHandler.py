import io
import aiohttp
import discord
import traceback

from discord import app_commands
from discord.ext import commands

from bot import CONFIG
import Source.Kernel.Views.Interface as Interface

class ErrorHandler(commands.Cog):
    """Global Error Handling"""
    def __init__(self, bot):
        self.bot = bot        
        
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):

        if hasattr(ctx.command, "on_error"):
            return

        error = getattr(error, "original", error)
    
        if isinstance(error, commands.CommandNotFound):
            return
        
        if isinstance(error, app_commands.errors.CommandNotFound):
            return

        if isinstance(error, commands.DisabledCommand):
            return await Interface.Traceback(self.bot, ctx, error).send(ctx)
    
        if  isinstance(error, commands.BotMissingPermissions):
            return await Interface.Traceback(self.bot, ctx, error).send(ctx)
        
        if isinstance(error, commands.MissingPermissions):
            return await Interface.Traceback(self.bot, ctx, error).send(ctx)
        
        if isinstance(error, commands.NoPrivateMessage):
            return await Interface.Traceback(self.bot, ctx, error).send(ctx)

        if isinstance(error, discord.errors.NotFound):
            return
    
        if isinstance(error, commands.NotOwner):
            return
        
        if isinstance(error, commands.MissingRequiredArgument):
            return await Interface.CommandSyntax(self.bot, ctx, error).send(ctx)
        
        if isinstance(error, commands.MemberNotFound):
            return await Interface.Traceback(self.bot, ctx, error).send(ctx)

        if isinstance(error, commands.BadArgument):
            return await Interface.CommandSyntax(self.bot, ctx, error).send(ctx)
           
        if isinstance(error, commands.errors.CommandOnCooldown):
            return await Interface.Traceback(self.bot, ctx, error).send(ctx)
        
        else:
            async with aiohttp.ClientSession() as session:
                error_webhook = discord.Webhook.partial(id = CONFIG.get("ERROR_ID"),token = CONFIG.get("ERROR_TOKEN"), session = session)
                if ctx.guild:
                    command_data = f"- Occured By    :   {ctx.author} / {ctx.author.id}\n" \
                                   f"- Command Name  :   {ctx.message.content}\n" \
                                   f"- @ Guild       :   {ctx.guild} / {ctx.guild.id}\n" \
                                   f"- @ Channel     :   {ctx.channel} / {ctx.channel.id}"
                else:
                    command_data = f"- Occured By    :   {ctx.author} /{ctx.author.id}\n" \
                                   f"- Command Name  :   {ctx.message.content}\n" \
                                   f"** Occured in DM's **"
                error_str = "".join(traceback.format_exception(type(error), error, error.__traceback__))
                error_emb = discord.Embed(
                    title = "Error Boi <:Pain:911261018582306867>",
                    description = f"```prolog\n{command_data} \n```\n```py\n {error_str}\n```",
                    colour = 0x2F3136)       
                error_emb.timestamp = discord.utils.utcnow()           
                send_error = error_webhook
                if len(error_str) < 2000:
                    try:
                        await send_error.send(embed = error_emb)
                        await send_error.send("||Break Point||")
                    except(discord.HTTPException, discord.Forbidden):
                        await send_error.send(embed = error_emb, file = discord.File(io.StringIO(error_str), filename = "Traceback.py"))
                        await send_error.send("||Break Point||")
                else:
                    await send_error.send(embed = error_emb, file = discord.File(io.StringIO(error_str), filename = "Traceback.py"))
                    await send_error.send("||Break Point||")
                    return 
                await session.close()

async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))