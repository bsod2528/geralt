from __future__ import annotations

from .developer import Developer
from ...kernel.subclasses.bot import Geralt

async def setup(bot: Geralt):
    await bot.add_cog(Developer(bot))