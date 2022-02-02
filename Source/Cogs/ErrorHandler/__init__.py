from __future__ import annotations

from .ErrorHandler import ErrorHandler

def setup(bot):
    bot.add_cog(ErrorHandler(bot))