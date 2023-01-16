from __future__ import annotations

from ...bot import BaseBot
from .moderation import Moderation


async def setup(bot: BaseBot):
    await bot.add_cog(Moderation(bot))
