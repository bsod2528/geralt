from __future__ import annotations

from .errorhandler import ErrorHandler

async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))