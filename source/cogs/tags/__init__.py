from __future__ import annotations

from .tags import Tags

async def setup(bot):
    await bot.add_cog(Tags(bot))