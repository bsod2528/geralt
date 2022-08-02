from typing import List

import source.kernel.views.fun as fun
import source.kernel.views.help as help
import source.kernel.views.meta as meta
import source.kernel.views.tags as tags
import source.kernel.subclasses.bot as bot
import source.kernel.utilities.flags as flags
import source.kernel.views.history as history
import source.kernel.views.tickets as tickets
import source.kernel.subclasses.embed as embed
import source.kernel.utilities.crucial as crucial
import source.kernel.views.paginator as paginator
import source.kernel.subclasses.context as context
import source.kernel.views.verification as verification
import source.kernel.views.errorhandler as errorhandler
import source.kernel.utilities.extensions as extensions
import source.kernel.subclasses.wavelink_player as player
import source.kernel.utilities.override_jsk as overidden_jishaku

COGS_EXTENSIONS: List = [
    "jishaku",
    "source.cogs.fun",
    "source.cogs.tags",
    "source.cogs.meta",
    "source.cogs.guild",
    # "source.cogs.music",
    "source.cogs.events",
    "source.cogs.utility",
    "source.cogs.developer",
    "source.cogs.moderation",
    "source.cogs.errorhandler"
]

KERNEL_EXTENSIONS: List = [
    bot,
    fun,
    help,
    meta,
    tags,
    flags,
    embed,
    player,
    history,
    tickets,
    crucial,
    context,
    paginator,
    extensions,
    verification,
    errorhandler,
    overidden_jishaku
]

# if cog == "kernel":
#            try:
#                for files in KERNEL_EXTENSIONS:
#                    reload(files)
#                return await ctx.reply(f"Reloaded <:RavenPray:914410353155244073>")
#            except Exception as exception:
#                async with ctx.channel.typing():
#                    await asyncio.sleep(0.1)
# return await ctx.reply(f"Couldn't reload all the kernel files :
# \n```py\n{exception}\n```", allowed_mentions=self.bot.mentions)
