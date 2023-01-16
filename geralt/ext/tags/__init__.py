from __future__ import annotations

from ...bot import BaseBot
from .tags import Tags


async def setup(bot: BaseBot):
    await bot.add_cog(Tags(bot))
