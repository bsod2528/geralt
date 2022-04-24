from __future__ import annotations

from .Developer import Developer

async def setup(bot):
    await bot.add_cog(Developer(bot))