from __future__ import annotations

from .Utility import Utility

def setup(bot):
    bot.add_cog(Utility(bot))