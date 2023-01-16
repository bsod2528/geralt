from __future__ import annotations

from ...bot import BaseBot
from .guild import Guild


async def setup(bot: BaseBot):
    await bot.add_cog(Guild(bot))
