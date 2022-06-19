from __future__ import annotations

from .meta import Meta
from ...kernel.subclasses.bot import Geralt

async def setup(bot : Geralt):
    await bot.add_cog(Meta(bot))