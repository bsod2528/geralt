from __future__ import annotations

from .moderation import Moderation
from ...kernel.subclasses.bot import Geralt

async def setup(bot: Geralt):
    await bot.add_cog(Moderation(bot))