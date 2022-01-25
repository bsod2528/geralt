import disnake

from disnake.ext import commands

import Source.Kernel.Views.Interface as UI
import Source.Kernel.Utilities.Flags as FLAGS
from Source.Kernel.Utilities.Crucial import EMOTE

class Information(commands.Cog):
    def __init__(self, bot):
        self.bot    =   bot

    @commands.command(
        name    =   "avatar",
        aliases =   ["pfp", "pp", "dp", "av"],
        brief   =   "View a persons PFP",
        help    =   "See the user's PFP in an enlarged manner")
    async def avatar(self, ctx, *, USER : disnake.Member = None):
        USER    =   USER or ctx.author
        PFP_EMB =   disnake.Embed(
            title   =   f"{str(USER)}'s Avatar",
            url =   USER.display_avatar.url,
            colour = self.bot.colour)
        user = USER or ctx.author
        avatar = user.display_avatar.with_static_format('png')
        PFP_EMB.set_image(url = avatar)
        PFP_EMB.timestamp = self.bot.Timestamp
        await ctx.reply(embed = PFP_EMB, mention_author = False, view = UI.PFP(ctx, self.bot))
def setup(bot):
    bot.add_cog(Information(bot))