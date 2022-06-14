from __future__ import annotations

from .meta import Meta

async def setup(bot):
    await bot.add_cog(Meta(bot))