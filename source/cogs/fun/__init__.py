from __future__ import annotations

from .fun import Fun
from ...kernel.subclasses.bot import Geralt


async def setup(bot: Geralt):
    await bot.add_cog(Fun(bot))
