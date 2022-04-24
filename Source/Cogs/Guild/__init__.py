from __future__ import annotations

from .Guild import Guild

async def setup(bot):
    await bot.add_cog(Guild(bot))