from __future__ import annotations

from .Events import Events

def setup(bot):
    bot.add_cog(Events(bot))