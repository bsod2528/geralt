from __future__ import annotations

from .Misc import Misc

async def setup(bot):
    await bot.add_cog(Misc(bot))