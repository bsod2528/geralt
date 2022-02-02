from __future__ import annotations

from .Slash import Slash

def setup(bot):
    bot.add_cog(Slash(bot))