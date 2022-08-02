from __future__ import annotations

from .music import Music
from ...kernel.subclasses.bot import Geralt


async def setup(bot: Geralt):
    await bot.add_cog(Music(bot))
