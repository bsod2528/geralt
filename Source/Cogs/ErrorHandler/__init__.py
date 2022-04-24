from __future__ import annotations

from .ErrorHandler import ErrorHandler

async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))