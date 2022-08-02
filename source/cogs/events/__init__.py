from __future__ import annotations

from .events import Events
from ...kernel.subclasses.bot import Geralt


async def setup(bot: Geralt):
    await bot.add_cog(Events(bot))
