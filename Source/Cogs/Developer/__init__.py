from __future__ import annotations

from .Developer import Developer

def setup(bot):
    bot.add_cog(Developer(bot))