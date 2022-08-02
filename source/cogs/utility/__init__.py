from __future__ import annotations

from .utility import Utility
from ...kernel.subclasses.bot import Geralt


async def setup(bot: Geralt):
    await bot.add_cog(Utility(bot))
