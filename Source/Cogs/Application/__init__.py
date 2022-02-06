from __future__ import annotations

from .Application import Application

def setup(bot):
    bot.add_cog(Application(bot))