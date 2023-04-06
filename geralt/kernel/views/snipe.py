from io import BytesIO
from typing import Optional

import discord
from discord import NotFound
from discord.ext import commands

from ...context import BaseContext


class SnipeStats(
    commands.FlagConverter, prefix="--", delimiter=" ", case_insensitive=True
):
    globalstats: Optional[bool]


class SnipeAttachmentViewer(discord.ui.View):
    def __init__(self, ctx: BaseContext, file_data: bytes, filename: str):
        super().__init__()
        self.ctx = ctx
        self.file_data = file_data
        self.filename = filename

    @discord.ui.button(label="Attachments", style=discord.ButtonStyle.grey)
    async def view_attachment(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        try:
            file_obj = discord.File(BytesIO(self.file_data), filename=self.filename)
            await interaction.response.send_message(file=file_obj, ephemeral=True)
        except Exception as e:
            print(e)

    async def on_timeout(self) -> None:
        try:
            for view in self.children:
                view.disabled = True
            await self.message.edit(view=self)
        except discord.NotFound:
            return


class EditSnipeAttachmentView(discord.ui.View):
    def __init__(
        self,
        ctx: BaseContext,
        pre_file_data: bytes,
        post_file_data: bytes,
        pre_filename: str,
        post_filename: str,
        # post_files: List[bytes],
        # post_filenames: List[str],
    ):
        super().__init__()
        self.ctx = ctx
        self.pre_file_data = pre_file_data
        self.post_file_data = post_file_data
        self.pre_filename = pre_filename
        self.post_filename = post_filename
        # self.post_files = post_files
        # self.post_filenames = post_filenames

    @discord.ui.button(label="Pre-Edit Attachments", style=discord.ButtonStyle.grey)
    async def view_preedit_attachments(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        try:
            file_obj = discord.File(
                BytesIO(self.pre_file_data), filename=self.pre_filename
            )
            await interaction.response.send_message(file=file_obj, ephemeral=True)
        except Exception as e:
            print(e)

    @discord.ui.button(label="Post-Edit Attachments", style=discord.ButtonStyle.grey)
    async def view_postedit_attachments(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        try:
            # if self.post_files:
            #     file_list: List[bytes] = []
            #     for file, filename in zip(self.post_files, self.post_filenames):
            #         file_list.append(discord.File(BytesIO(file), filename=filename))
            #     return await interaction.response.send_message(files=file_list)
            file_obj = discord.File(
                BytesIO(self.post_file_data), filename=self.post_filename
            )
            await interaction.response.send_message(file=file_obj, ephemeral=True)
        except Exception as e:
            print(e)

    async def on_timeout(self) -> None:
        try:
            for view in self.children:
                view.disabled = True
            await self.from_message
        except NotFound:
            return
