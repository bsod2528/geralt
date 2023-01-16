from __future__ import annotations

from ...bot import BaseBot
from .meta import Meta


async def setup(bot: BaseBot):
    await bot.add_cog(Meta(bot))
