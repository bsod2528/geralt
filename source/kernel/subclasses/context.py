import discord

from discord.ext import commands
from discord.utils import MISSING
from typing import Any, Union, Optional, Sequence, TYPE_CHECKING

from .embed import BaseEmbed

if TYPE_CHECKING:
    from .bot import Geralt


class GeraltContext(commands.Context["Geralt"]):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def __repr__(self) -> str:
        return "<Context>"

    async def command_help(self) -> commands.HelpCommand.send_group_help:
        return await self.send_help(self.command)

    async def add_nanotick(self) -> discord.Emoji:
        try:
            await self.message.add_reaction("<:NanoTick:925271358735257651>")
        except BaseException:
            return

    async def add_nanocross(self) -> discord.Emoji:
        try:
            await self.message.add_reaction("<:NanoCross:965845144307912754>")
        except BaseException:
            return

    async def send(
            self, content: Optional[str] = None, *, tts: bool = False, embed: Optional[BaseEmbed] = None, embeds: Optional[Sequence[BaseEmbed]] = None, file: Optional[discord.File] = None, files: Optional[Sequence[discord.File]] = None, stickers: Optional[Sequence[Union[discord.GuildSticker, discord.StickerItem]]] = None,
            delete_after: Optional[float] = None, nonce: Optional[Union[str, int]] = None, allowed_mentions: Optional[discord.AllowedMentions] = None, reference: Optional[Union[discord.Message, discord.MessageReference, discord.PartialMessage]] = None, mention_author: Optional[bool] = None, view: Optional[discord.ui.View] = None, suppress_embeds: bool = False, ephemeral: bool = False) -> discord.Message:

        if self.interaction is None or self.interaction.is_expired():
            return await super().send(
                content=content, tts=tts, embed=embed, embeds=embeds, file=file, files=files, stickers=stickers, delete_after=delete_after,
                nonce=nonce, allowed_mentions=allowed_mentions, reference=reference, mention_author=mention_author, view=view, suppress_embeds=suppress_embeds)

        kwargs = {
            "content": content,
            "tts": tts,
            "embed": MISSING if embed is None else embed,
            "embeds": MISSING if embeds is None else embeds,
            "file": MISSING if file is None else file,
            "files": MISSING if files is None else files,
            "allowed_mentions": MISSING if allowed_mentions is None else allowed_mentions,
            "view": MISSING if view is None else view,
            "suppress_embeds": suppress_embeds,
            "ephemeral": ephemeral,
        }

        if self.interaction:
            return await super().send(
                content=content, tts=tts, embed=embed, embeds=embeds, file=file, files=files, stickers=stickers, delete_after=delete_after, nonce=nonce,
                allowed_mentions=allowed_mentions, reference=reference, mention_author=mention_author, view=view, suppress_embeds=suppress_embeds, ephemeral=True)

        if self.interaction.response.is_done():
            msg = await self.interaction.followup.send(**kwargs, wait=True)
        else:
            await self.interaction.response.send_message(**kwargs)
            msg = await self.interaction.original_message()

        if delete_after is not None and not (
                ephemeral and self.interaction is not None):
            await msg.delete(delay=delete_after)
        return msg

    async def reply(self, content: Optional[str] = None, **kwargs: Any) -> discord.Message:
        if self.interaction:
            return await self.send(content, reference=self.message, **kwargs)
        if self.interaction is None:
            return await self.send(content, reference=self.message, **kwargs)
        else:
            return await self.send(content, **kwargs)
