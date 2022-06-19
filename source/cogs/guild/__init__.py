from __future__ import annotations

from .guild import Guild
from ...kernel.subclasses.bot import Geralt

async def setup(bot : Geralt):
    await bot.add_cog(Guild(bot))