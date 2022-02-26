from __future__ import annotations

from .Help import CustomHelp

def setup(bot):
    bot.add_cog(CustomHelp(bot))