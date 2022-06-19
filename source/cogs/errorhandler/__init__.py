from __future__ import annotations

from .errorhandler import ErrorHandler
from ...kernel.subclasses.bot import Geralt

async def setup(bot : Geralt):
    await bot.add_cog(ErrorHandler(bot))