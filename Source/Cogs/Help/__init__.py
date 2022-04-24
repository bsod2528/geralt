from __future__ import annotations

from .Help import CustomHelp

async def setup(bot):
    await bot.add_cog(CustomHelp(bot))