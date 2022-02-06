from __future__ import annotations

from .Guild import Guild

def setup(bot):
    bot.add_cog(Guild(bot))