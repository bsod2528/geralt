from __future__ import annotations

from .Moderation import Moderation

async def setup(bot):
    await bot.add_cog(Moderation(bot))