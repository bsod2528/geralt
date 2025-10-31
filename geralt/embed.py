"""Embed helpers used throughout the Geralt bot."""

import discord


class BaseEmbed(discord.Embed):
    """Default embed with a UTC timestamp preset.

    The timestamp ensures embeds remain consistent across the bot without
    every caller repeating the same boilerplate.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # `discord.Embed` only sets ``timestamp`` when provided explicitly, so
        # we keep our embeds anchored to the moment they are instantiated.
        self.timestamp = discord.utils.utcnow()

    def __repr__(self) -> str:
        return "<geralt.BaseEmbed>"
