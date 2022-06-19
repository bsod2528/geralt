from __future__ import annotations

from .help import Help
from ...kernel.subclasses.bot import Geralt

async def setup(bot : Geralt):
    await bot.add_cog(Help(bot))