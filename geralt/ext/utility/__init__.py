from __future__ import annotations

from ...bot import BaseBot
from .utility import Utility


async def setup(bot: BaseBot):
    await bot.add_cog(Utility(bot))
