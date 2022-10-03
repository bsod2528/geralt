from __future__ import annotations

from .discord_utils import Discord

from ...kernel.subclasses.bot import Geralt


async def setup(bot: Geralt):
    await bot.add_cog(Discord(bot))