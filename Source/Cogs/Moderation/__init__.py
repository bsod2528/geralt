from __future__ import annotations

from .Moderation import Moderation

def setup(bot):
    bot.add_cog(Moderation(bot))