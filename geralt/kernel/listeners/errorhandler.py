import io
import traceback

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from ...bot import CONFIG, BaseBot
from ...context import BaseContext
from ...embed import BaseEmbed
from ..views.errorhandler import CommandSyntax, Traceback


class ErrorHandler(commands.Cog):
    """Global Error Handling"""

    def __init__(self, bot: BaseBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: BaseContext, error: Exception):
        if hasattr(ctx.command, "on_error"):
            return

        error = getattr(error, "original", error)

        if isinstance(error, commands.NotOwner):
            return

        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, app_commands.AppCommandError):
            return await Traceback(self.bot, ctx, error).send()

        if isinstance(error, commands.errors.MaxConcurrencyReached):
            return await Traceback(self.bot, ctx, error).send()

        if isinstance(error, app_commands.errors.CommandNotFound):
            return

        if isinstance(error, commands.DisabledCommand):
            return await Traceback(self.bot, ctx, error).send()

        if isinstance(error, commands.BotMissingPermissions):
            return await Traceback(self.bot, ctx, error).send()

        if isinstance(error, commands.MissingPermissions):
            return await Traceback(self.bot, ctx, error).send()

        if isinstance(error, commands.NoPrivateMessage):
            return await Traceback(self.bot, ctx, error).send()

        if isinstance(error, commands.MemberNotFound):
            return await Traceback(self.bot, ctx, error).send()

        if isinstance(error, commands.BadArgument):
            return await Traceback(self.bot, ctx, error).send()

        if isinstance(error, commands.errors.CommandOnCooldown):
            return await Traceback(self.bot, ctx, error).send()

        if isinstance(error, commands.MissingRequiredArgument):
            return await CommandSyntax(self.bot, ctx, error).send()

        else:
            async with aiohttp.ClientSession() as session:
                error_webhook = discord.Webhook.partial(
                    id=CONFIG.get("ERROR_ID"),
                    token=CONFIG.get("ERROR_TOKEN"),
                    session=session,
                )
                if ctx.guild:
                    command_data = (
                        f"- Occured By    :   {ctx.author} / {ctx.author.id}\n"
                        f"- Command Name  :   {ctx.message.content}\n"
                        f"- @ Guild       :   {ctx.guild} / {ctx.guild.id}\n"
                        f"- @ Channel     :   {ctx.channel} / {ctx.channel.id}"
                    )
                else:
                    command_data = (
                        f"- Occured By    :   {ctx.author} /{ctx.author.id}\n"
                        f"- Command Name  :   {ctx.message.content}\n"
                        f"** Occured in DM's **"
                    )
                error_str = "".join(
                    traceback.format_exception(type(error), error, error.__traceback__)
                )
                error_emb = BaseEmbed(
                    title="Error Boi <:Pain:911261018582306867>",
                    description=f"[**Jump Url**]({ctx.message.jump_url})```prolog\n{command_data} \n```\n```py\n {error_str}\n```",
                    colour=0x2F3136,
                )
                view = discord.ui.View()
                view.add_item(
                    discord.ui.Button(
                        label="Jump",
                        style=discord.ButtonStyle.url,
                        url=ctx.message.jump_url,
                    )
                )
                send_error = error_webhook
                if len(error_str) < 2000:
                    try:
                        await send_error.send(embed=error_emb)
                        await send_error.send("||Break Point||")
                    except (discord.HTTPException, discord.Forbidden):
                        await send_error.send(
                            embed=error_emb,
                            file=discord.File(
                                io.StringIO(error_str), filename="traceback.py"
                            ),
                        )
                        await send_error.send("||Break Point||")
                else:
                    await send_error.send(
                        embed=error_emb,
                        file=discord.File(
                            io.StringIO(error_str), filename="traceback.py"
                        ),
                    )
                    await send_error.send("||Break Point||")
                    return
                await session.close()


async def setup(bot: BaseBot):
    await bot.add_cog(ErrorHandler(bot))
