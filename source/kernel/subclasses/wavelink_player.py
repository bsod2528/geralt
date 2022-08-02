import discord
import wavelink

from typing import TYPE_CHECKING

from .embed import BaseEmbed

if TYPE_CHECKING:
    from .bot import Geralt
    from .context import GeraltContext


class GeraltPlayer(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __repr__(self) -> str:
        return "<Geralt's Wavelink Player>"
