from __future__ import annotations

from .tags import Tags
from ...kernel.subclasses.bot import Geralt

async def setup(bot : Geralt):
    await bot.add_cog(Tags(bot))