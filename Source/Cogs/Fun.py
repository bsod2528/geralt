import disnake

from disnake.ext import commands

import Source.Kernel.Utilities.Crucial as CRUCIAL

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot    =   bot

    @commands.command(
        name    =   "as", 
        brief   =   "Send a Webhook",
        help    =   "Send a webhook message as the user you mentioned")
    async def webhoo(self, ctx, USER : disnake.Member, *, MESSAGE):
        WBHK = await CRUCIAL.FETCH_WEBHOOK(ctx.channel)
        thread = disnake.utils.MISSING
        if isinstance(ctx.channel, disnake.Thread):
            thread = ctx.channel
        await WBHK.send(
            MESSAGE, 
            avatar_url  =   USER.display_avatar.url, 
            username    =   USER.display_name, 
            thread      =   thread)
        await ctx.message.delete(delay = 0)

def setup(bot):
    bot.add_cog(Fun(bot))