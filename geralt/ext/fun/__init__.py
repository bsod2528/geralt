from __future__ import annotations

from ...bot import BaseBot
from .fun import Fun


async def setup(bot: BaseBot):
    await bot.add_cog(Fun(bot))
