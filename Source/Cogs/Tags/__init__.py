from __future__ import annotations

from .Tags import Tags

async def setup(bot):
    await bot.add_cog(Tags(bot))