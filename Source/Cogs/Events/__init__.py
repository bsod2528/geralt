from __future__ import annotations

from .Events import Events

async def setup(bot):
    await bot.add_cog(Events(bot))