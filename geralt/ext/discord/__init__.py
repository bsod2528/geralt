from __future__ import annotations

from ...bot import BaseBot
from .discord_utils import Discord


async def setup(bot: BaseBot):
    await bot.add_cog(Discord(bot))
