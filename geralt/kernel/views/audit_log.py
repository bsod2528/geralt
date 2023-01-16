from typing import List, Any, Optional

import discord
from discord import AuditLogAction
from discord.utils import MISSING
from discord.ui.item import Item
from discord.errors import NotFound, HTTPException

from ...bot import BaseBot
from ...embed import BaseEmbed
from ...context import BaseContext


class MainAuditLog(discord.ui.View):
    def __init__(
            self,
            bot: BaseBot,
            ctx: BaseContext,
            sent_message_id: discord.Message):
        super().__init__(timeout=180)
        self.bot: BaseBot = bot
        self.ctx: BaseContext = ctx
        self.sent_message_id: discord.Message = sent_message_id

        self.footer: BaseEmbed.footer = f"Invoked by: {ctx.author}"
        self.icon_url: discord.User.display_avatar = ctx.author.display_avatar.url

        self.clear_items()
        self.add_item(self._select)

    options: List[discord.SelectOption] = [
        discord.SelectOption(label="Members", value="members", description="on the nembers.", emoji="<:Members:1044584952873898066>"),
        discord.SelectOption(label="Moderation", value="mod", description="moderation activites occurred.", emoji="<:BanHammer:1044586305213972590>"),
        discord.SelectOption(label="Emotes", value="emotes", description="all the emotes .", emoji="<:Emote:1044584258578157588>"),
        discord.SelectOption(label="Stickers", value="stickers", description="all the stickers.", emoji="<:Sticker:1044997709981032479>"),
        discord.SelectOption(label="Messages", value="messages", description="the messages sent.", emoji="<a:Typing:1044587029272461422>")]

    @discord.ui.select(placeholder="Actions taken on / related to . . .",
                       options=options, max_values=1, min_values=1, row=1)
    async def _select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if select.values[0] == "members":
            try:
                self.clear_items()
                self.add_item(self._select)
                self.add_item(self.member_move)
                self.add_item(self.member_update)
                self.add_item(self.member_role_update)
                self.add_item(self.member_disconnected)
                await interaction.response.edit_message(view=self)
            except (NotFound, HTTPException):
                return
        if select.values[0] == "emotes":
            try:
                self.clear_items()
                self.add_item(self._select)
                self.add_item(self.emote_create)
                self.add_item(self.emote_update)
                self.add_item(self.emote_delete)
                await interaction.response.edit_message(view=self)
            except (NotFound, HTTPException):
                return
        if select.values[0] == "stickers":
            try:
                self.clear_items()
                self.add_item(self._select)
                self.add_item(self.sticker_create)
                self.add_item(self.sticker_update)
                self.add_item(self.sticker_delete)
                await interaction.response.edit_message(view=self)
            except (NotFound, HTTPException):
                return
        if select.values[0] == "mod":
            try:
                self.clear_items()
                self.add_item(self._ban)
                self.add_item(self._kick)
                self.add_item(self._unban)
                self.add_item(self._select)
                self.add_item(self.member_prune)
                await interaction.response.edit_message(view=self)
            except (NotFound, HTTPException):
                return
        if select.values[0] == "messages":
            try:
                self.clear_items()
                self.add_item(self._select)
                self.add_item(self.message_pin)
                self.add_item(self.message_unpin)
                self.add_item(self.message_delete)
                self.add_item(self.message_bulk_delete)
                await interaction.response.edit_message(view=self)
            except (NotFound, HTTPException):
                return

    # if self._select.select.values[0] == "members"
    @discord.ui.button(label="Member Move", style=discord.ButtonStyle.grey)
    async def member_move(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            member_move_emb = BaseEmbed(
                description=f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nIterating through the audit log takes time,\n please be patient once you've pressed a button",
                colour=0xff6464)
            member_move_emb.set_footer(
                text=self.footer, icon_url=self.icon_url)

            async for log in self.ctx.guild.audit_logs(limit=None):
                if log.action is AuditLogAction.member_move:
                    member_move_emb.add_field(
                        name="Member Moved",
                        value=f"` - ` {log.user.mention} moved a total of **`{log.extra.count}`** member{'' if log.extra.count == 1 else 's'} to <#{log.extra.channel.id}>\n` - ` Occured: {self.bot.timestamp(log.created_at, style='R')}",
                        inline=False)

                    if len(member_move_emb.fields) > 3:
                        break
                    if len(member_move_emb.fields) == 0:
                        member_move_emb.description = f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nThere are no records for `moving members` from one voice channel to another."
                await interaction.followup.edit_message(embed=member_move_emb, message_id=self.sent_message_id)
        except (NotFound, HTTPException):
            return

    @discord.ui.button(label="Nickname Changes",
                       style=discord.ButtonStyle.grey)
    async def member_update(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            nickaname_changes_emb = BaseEmbed(
                description=f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nIterating through the audit log takes time,\n please be patient once you've pressed a button",
                colour=0xff6464)
            nickaname_changes_emb.set_footer(
                text=self.footer, icon_url=self.icon_url)

            async for log in self.ctx.guild.audit_logs(limit=None):
                if log.action is AuditLogAction.member_update:
                    before_nickname: Optional[str] = getattr(
                        log.before, "nick", MISSING)
                    after_nickname: Optional[str] = getattr(
                        log.after, "nick", MISSING)

                    if before_nickname is None:
                        before_nickname = f"`{log.target}`"
                    else:
                        before_nickname = f"`{before_nickname}`"
                    if after_nickname is None:
                        after_nickname = f"`{log.target}`"
                    else:
                        after_nickname = f"`{after_nickname}`"

                    nickaname_changes_emb.add_field(
                        name="Nickname Changed",
                        value=f"` - ` `{log.user}` changed `{log.target}` 's nickname.\n` - ` Before: {before_nickname} **|** After: {after_nickname}\n` - ` Occured: {self.bot.timestamp(log.created_at, style='R')}",
                        inline=False)
                    if len(nickaname_changes_emb.fields) > 3:
                        break
                    if len(nickaname_changes_emb.fields) == 0:
                        nickaname_changes_emb.description = f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nThere are no records for `changing nicknames` for any of the members."
                    await interaction.followup.edit_message(embed=nickaname_changes_emb, message_id=self.sent_message_id)
        except (NotFound, HTTPException):
            return

    @discord.ui.button(label="Role Update", style=discord.ButtonStyle.grey)
    async def member_role_update(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            role_update_emb = BaseEmbed(
                description=f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nIterating through the audit log takes time,\n please be patient once you've pressed a button",
                colour=0xff6464)
            role_update_emb.set_footer(
                text=self.footer, icon_url=self.icon_url)

            async for log in self.ctx.guild.audit_logs(limit=None):
                if log.action is AuditLogAction.member_role_update:
                    before_role: Optional[List[discord.Role]] = getattr(
                        log.before, "roles", MISSING)
                    after_role: Optional[List[discord.Role]] = getattr(
                        log.after, "roles", MISSING)
                    if len(before_role) == 0:
                        before_role = "`No Role`"
                    else:
                        before_role = f"{before_role[0].mention}"
                    if len(after_role) == 0:
                        after_role = "`No Role`"
                    else:
                        after_role = f"{after_role[0].mention}"

                    role_update_emb.add_field(
                        name="Roles Updated",
                        value=f"` - ` {log.user.mention} changed `{log.target}`'s nickname.\n` - ` Before: {before_role} **|** After: {after_role}\n` - ` Occured: {self.bot.timestamp(log.created_at, style='R')}",
                        inline=False)
                    if len(role_update_emb.fields) > 3:
                        break
                    if len(role_update_emb.fields) == 0:
                        role_update_emb.description = f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nThere are no records for `updating roles` for any of the members."
                await interaction.followup.edit_message(embed=role_update_emb, message_id=self.sent_message_id)
        except (NotFound, HTTPException):
            return

    @discord.ui.button(label="Member Disconnected",
                       style=discord.ButtonStyle.grey)
    async def member_disconnected(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            member_disconnected_emb = BaseEmbed(
                description=f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nIterating through the audit log takes time,\n please be patient once you've pressed a button",
                colour=0xff6464)
            member_disconnected_emb.set_footer(
                text=self.footer, icon_url=self.icon_url)

            async for log in self.ctx.guild.audit_logs(limit=None):
                if log.action is AuditLogAction.member_disconnect:
                    member_disconnected_emb.add_field(
                        name="Member Disconnected",
                        value=f"` - ` A total of __`{log.extra.count}`__ member{'' if log.extra.count == 1 else 's'} left voice channel\n` - ` Occured: {self.bot.timestamp(log.created_at, style='R')}",
                        inline=False)

                    if len(member_disconnected_emb.fields) > 3:
                        break
                    if len(member_disconnected_emb.fields) == 0:
                        member_disconnected_emb.description = f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nThere are no records for `disconnecting members` from any voice channel"
                await interaction.followup.edit_message(embed=member_disconnected_emb, message_id=self.sent_message_id)
        except (NotFound, HTTPException):
            return

    # if self._select.select.values[0] == "emoji"
    @discord.ui.button(label="Emote Create", style=discord.ButtonStyle.grey)
    async def emote_create(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            emote_create_emb = BaseEmbed(
                description=f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nIterating through the audit log takes time,\n please be patient once you've pressed a button",
                colour=0xff6464)
            emote_create_emb.set_footer(
                text=self.footer, icon_url=self.icon_url)

            async for log in self.ctx.guild.audit_logs(limit=None):
                if log.action is AuditLogAction.emoji_create:
                    emote_create_emb.add_field(
                        name="Emote Added",
                        value=f"` - ` {log.user.mention} created an emote named [**`{log.target.name}`**]({log.target.url}): {log.target}\n` - ` Occured: {self.bot.timestamp(log.created_at, style='R')}",
                        inline=False)

                    if len(emote_create_emb.fields) > 3:
                        break
                    if len(emote_create_emb.fields) == 0:
                        emote_create_emb.description = f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nThere are no records for `creating emotes`."
                await interaction.followup.edit_message(embed=emote_create_emb, message_id=self.sent_message_id)
        except (NotFound, HTTPException):
            return

    @discord.ui.button(label="Emote Update", style=discord.ButtonStyle.grey)
    async def emote_update(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            emote_update_emb = BaseEmbed(
                description=f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nIterating through the audit log takes time,\n please be patient once you've pressed a button",
                colour=0xff6464)
            emote_update_emb.set_footer(
                text=self.footer, icon_url=self.icon_url)

            async for log in self.ctx.guild.audit_logs(limit=None):
                if log.action is AuditLogAction.emoji_update:
                    emote_update_emb.add_field(
                        name="Emote Updated",
                        value=f"` - ` {log.target} emote's name got changed by {log.user.mention}\n` - ` Before: `{log.before.name}` **|** After: `{log.after.name}`\n` - ` Occured: {self.bot.timestamp(log.created_at, style='R')}",
                        inline=False)

                    if len(emote_update_emb.fields) > 3:
                        break
                    if len(emote_update_emb.fields) == 0:
                        emote_update_emb.description = f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nThere are no records for `updating emotes`."
            await interaction.followup.edit_message(embed=emote_update_emb, message_id=self.sent_message_id)
        except (NotFound, HTTPException):
            return

    @discord.ui.button(label="Emote Delete", style=discord.ButtonStyle.grey)
    async def emote_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            emote_delete_emb = BaseEmbed(
                description=f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nIterating through the audit log takes time,\n please be patient once you've pressed a button",
                colour=0xff6464)
            emote_delete_emb.set_footer(
                text=self.footer, icon_url=self.icon_url)

            async for log in self.ctx.guild.audit_logs(limit=None):
                if log.action is AuditLogAction.emoji_update:
                    emote_delete_emb.add_field(
                        name="Emote Deleted",
                        value=f"` - ` `{log.before.name}` emote was deleted by by {log.user.mention}\n` - ` Occured: {self.bot.timestamp(log.created_at, style='R')}",
                        inline=False)

                    if len(emote_delete_emb.fields) > 3:
                        break
                    if len(emote_delete_emb.fields) == 0:
                        emote_delete_emb.description = f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nThere are no records for `deleting emotes`."
            await interaction.followup.edit_message(embed=emote_delete_emb, message_id=self.sent_message_id)
        except (NotFound, HTTPException):
            return

    # if self._select.select.values[0] == "stickers"
    @discord.ui.button(label="Sticker Create", style=discord.ButtonStyle.grey)
    async def sticker_create(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            sticker_create_emb = BaseEmbed(
                description=f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nIterating through the audit log takes time,\n please be patient once you've pressed a button",
                colour=0xff6464)
            sticker_create_emb.set_footer(
                text=self.footer, icon_url=self.icon_url)

            async for log in self.ctx.guild.audit_logs(limit=None):
                if log.action is AuditLogAction.sticker_create:
                    sticker_create_emb.add_field(
                        name="Sticker Created",
                        value=f"` - ` {log.user.mention} created a sticker [__**`{log.target.name}`**__]({log.target.url}) with :{log.target.emoji}: as trigger which is `{'available' if log.target.available == True else 'not available'}`.\n` - ` Occured: {self.bot.timestamp(log.created_at, style='R')}",
                        inline=False)

                    if len(sticker_create_emb.fields) > 3:
                        break
                    if len(sticker_create_emb.fields) == 0:
                        sticker_create_emb.description = f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nThere are no records for `creating stickers`."
            await interaction.followup.edit_message(embed=sticker_create_emb, message_id=self.sent_message_id)
        except (NotFound, HTTPException):
            return

    @discord.ui.button(label="Sticker Update", style=discord.ButtonStyle.grey)
    async def sticker_update(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            sticker_update_emb = BaseEmbed(
                description=f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nIterating through the audit log takes time,\n please be patient once you've pressed a button",
                colour=0xff6464)
            sticker_update_emb.set_footer(
                text=self.footer, icon_url=self.icon_url)

            async for log in self.ctx.guild.audit_logs(limit=None):
                if log.action is AuditLogAction.sticker_update:
                    sticker_update_emb.add_field(
                        name="Sticker Updated",
                        value=f"` - ` {log.user.mention} changed `{log.target.name}`'s name from: **`{log.before.name}`** to **`{log.after.name}`**.\n` - ` Occured: {self.bot.timestamp(log.created_at, style='R')}",
                        inline=False)

                    if len(sticker_update_emb.fields) > 3:
                        break
                    if len(sticker_update_emb.fields) == 0:
                        sticker_update_emb.description = f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nThere are no records for `updating stickers`."
            await interaction.followup.edit_message(embed=sticker_update_emb, message_id=self.sent_message_id)
        except (NotFound, HTTPException):
            return

    @discord.ui.button(label="Sticker Delete", style=discord.ButtonStyle.grey)
    async def sticker_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            sticker_delete_emb = BaseEmbed(
                description=f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nIterating through the audit log takes time,\n please be patient once you've pressed a button",
                colour=0xff6464)
            sticker_delete_emb.set_footer(
                text=self.footer, icon_url=self.icon_url)

            async for log in self.ctx.guild.audit_logs(limit=None):
                if log.action is AuditLogAction.sticker_delete:
                    sticker_delete_emb.add_field(
                        name="Sticker Deleted",
                        value=f"` - ` {log.user.mention} deleted __**`{log.before.name}`**__ sticker.\n` - ` Occured: {self.bot.timestamp(log.created_at, style='R')}",
                        inline=False)

                    if len(sticker_delete_emb.fields) > 3:
                        break
                    if len(sticker_delete_emb.fields) == 0:
                        sticker_delete_emb.description = f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nThere are no records for `deleting stickers`."
            await interaction.followup.edit_message(embed=sticker_delete_emb, message_id=self.sent_message_id)
        except (NotFound, HTTPException):
            return

    # if self._select.select.value[0] == "mod"
    @discord.ui.button(label="Kick", style=discord.ButtonStyle.grey)
    async def _kick(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            kick_emb = BaseEmbed(
                description=f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nIterating through the audit log takes time,\n please be patient once you've pressed a button",
                colour=0xff6464)
            kick_emb.set_footer(text=self.footer, icon_url=self.icon_url)

            async for log in self.ctx.guild.audit_logs(limit=None):
                if log.action is AuditLogAction.kick:
                    kick_emb.add_field(
                        name="Member Kicked",
                        value=f"` - ` {log.user.mention} kicked **`{log.target}`** for `{log.reason if log.reason else 'unspecified reason'}`\n` - ` Occured: {self.bot.timestamp(log.created_at, style='R')}",
                        inline=False)

                    if len(kick_emb.fields) > 3:
                        break
                    if len(kick_emb.fields) == 0:
                        kick_emb.description = f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nThere are no records of `kicking` any user."
            await interaction.followup.edit_message(embed=kick_emb, message_id=self.sent_message_id)
        except (NotFound, HTTPException):
            return

    @discord.ui.button(label="Ban", style=discord.ButtonStyle.grey)
    async def _ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            ban_emb = BaseEmbed(
                description=f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nIterating through the audit log takes time,\n please be patient once you've pressed a button",
                colour=0xff6464)
            ban_emb.set_footer(text=self.footer, icon_url=self.icon_url)

            async for log in self.ctx.guild.audit_logs(limit=None):
                if log.action is AuditLogAction.ban:
                    ban_emb.add_field(
                        name="Member Banned",
                        value=f"` - ` {log.user.mention} banned **`{log.target}`** for `{log.reason if log.reason else 'unspecified reason'}`\n` - ` Occured: {self.bot.timestamp(log.created_at, style='R')}",
                        inline=False)

                    if len(ban_emb.fields) > 3:
                        break
                    if len(ban_emb.fields) == 0:
                        ban_emb.description = f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nThere are no records of `banning` any user."
            await interaction.followup.edit_message(embed=ban_emb, message_id=self.sent_message_id)
        except (NotFound, HTTPException):
            return

    @discord.ui.button(label="Unban", style=discord.ButtonStyle.grey)
    async def _unban(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            unban_emb = BaseEmbed(
                description=f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nIterating through the audit log takes time,\n please be patient once you've pressed a button",
                colour=0xff6464)
            unban_emb.set_footer(text=self.footer, icon_url=self.icon_url)

            async for log in self.ctx.guild.audit_logs(limit=None):
                if log.action is AuditLogAction.unban:
                    unban_emb.add_field(
                        name="Member Unbanned",
                        value=f"` - ` {log.user.mention} unbanned __**`{log.target}`**__\n` - ` Occured: {self.bot.timestamp(log.created_at, style='R')}",
                        inline=False)

                    if len(unban_emb.fields) > 3:
                        break
                    if len(unban_emb.fields) == 0:
                        unban_emb.description = f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nThere are no records of `unbanning` any user."
            await interaction.followup.edit_message(embed=unban_emb, message_id=self.sent_message_id)
        except (NotFound, HTTPException):
            return

    @discord.ui.button(label="Prune", style=discord.ButtonStyle.grey)
    async def member_prune(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            member_prune_emb = BaseEmbed(
                description=f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nIterating through the audit log takes time,\n please be patient once you've pressed a button",
                colour=0xff6464)
            member_prune_emb.set_footer(
                text=self.footer, icon_url=self.icon_url)

            async for log in self.ctx.guild.audit_logs(limit=None):
                if log.action is AuditLogAction.member_prune:
                    member_prune_emb.add_field(
                        name="Member(s) Pruned",
                        value=f"` - ` {log.user.mention} pruned for `{log.extra.delete_member_days}` days. __**`{log.extra.members_removed}`**__ member{'' if log.extra.members_removed == 1 else 's'} were removed\n` - ` Occured: {self.bot.timestamp(log.created_at, style='R')}",
                        inline=False)

                    if len(member_prune_emb.fields) > 3:
                        break
                    if len(member_prune_emb.fields) == 0:
                        member_prune_emb.description = f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nThere are no records of `pruning` any user."
            await interaction.followup.edit_message(embed=member_prune_emb, message_id=self.sent_message_id)
        except (NotFound, HTTPException):
            return

    # if self._select.select.values[0] == "messages"
    @discord.ui.button(label="Message Pin", style=discord.ButtonStyle.grey)
    async def message_pin(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            message_pin_emb = BaseEmbed(
                description=f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nIterating through the audit log takes time,\n please be patient once you've pressed a button",
                colour=0xff6464)
            message_pin_emb.set_footer(
                text=self.footer, icon_url=self.icon_url)

            async for log in self.ctx.guild.audit_logs(limit=None):
                if log.action is AuditLogAction.message_pin:
                    message_pin_emb.add_field(
                        name="Message Pinned",
                        value=f"` - ` {log.user.mention} pinned __**`{log.target}`**__'s [`message`](https://discord.com/channels/{self.ctx.guild.id}/{log.extra.channel.id}/{log.extra.message_id}) in {log.extra.channel.mention}\n` - ` Occured: {self.bot.timestamp(log.created_at, style='R')}",
                        inline=False)

                    if len(message_pin_emb.fields) > 3:
                        break
                    if len(message_pin_emb.fields) == 0:
                        message_pin_emb.description = f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nThere are no records of `pinning messages` of any user."
            await interaction.followup.edit_message(embed=message_pin_emb, message_id=self.sent_message_id)
        except (NotFound, HTTPException):
            return

    @discord.ui.button(label="Message Unpin", style=discord.ButtonStyle.grey)
    async def message_unpin(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            message_unpin_emb = BaseEmbed(
                description=f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nIterating through the audit log takes time,\n please be patient once you've pressed a button",
                colour=0xff6464)
            message_unpin_emb.set_footer(
                text=self.footer, icon_url=self.icon_url)

            async for log in self.ctx.guild.audit_logs(limit=None):
                if log.action is AuditLogAction.message_unpin:
                    message_unpin_emb.add_field(
                        name="Message Unpinned",
                        value=f"` - ` {log.user.mention} unpined __**`{log.target}`**__ [`message`](https://discord.com/channels/{self.ctx.guild.id}/{log.extra.channel.id}/{log.extra.message_id}) in {log.extra.channel.mention}\n` - ` Occured: {self.bot.timestamp(log.created_at, style='R')})",
                        inline=False)

                    if len(message_unpin_emb.fields) > 3:
                        break
                    if len(message_unpin_emb.fields) == 0:
                        message_unpin_emb.description = f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nThere are no records of `unpinning messages` of any user."
            await interaction.followup.edit_message(embed=message_unpin_emb, message_id=self.sent_message_id)
        except (NotFound, HTTPException):
            return

    @discord.ui.button(label="Message Delete", style=discord.ButtonStyle.grey)
    async def message_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            message_delete_emb = BaseEmbed(
                description=f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nIterating through the audit log takes time,\n please be patient once you've pressed a button",
                colour=0xff6464)
            message_delete_emb.set_footer(
                text=self.footer, icon_url=self.icon_url)

            async for log in self.ctx.guild.audit_logs(limit=None):
                if log.action is AuditLogAction.message_delete:
                    message_delete_emb.add_field(
                        name="Message Deleted",
                        value=f"` - ` {log.user.mention} deleted `{log.extra.count}` message{'' if log.extra.count == 1 else 's'} sent by __**`{log.target}`**__ in {log.extra.channel.mention}\n` - ` Occured: {self.bot.timestamp(log.created_at, style='R')}",
                        inline=False)

                    if len(message_delete_emb.fields) > 3:
                        break
                    if len(message_delete_emb.fields) == 0:
                        message_delete_emb.description = f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nThere are no records of `deleting` any message."
            await interaction.followup.edit_message(embed=message_delete_emb, message_id=self.sent_message_id)
        except (NotFound, HTTPException):
            return

    @discord.ui.button(label="Message Bulk Delete",
                       style=discord.ButtonStyle.grey)
    async def message_bulk_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            message_bulk_delete_emb = BaseEmbed(
                description=f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nIterating through the audit log takes time,\n please be patient once you've pressed a button",
                colour=0xff6464)
            message_bulk_delete_emb.set_footer(
                text=self.footer, icon_url=self.icon_url)

            async for log in self.ctx.guild.audit_logs(limit=None):
                if log.action is AuditLogAction.message_bulk_delete:
                    message_bulk_delete_emb.add_field(
                        name="Bulk Messages Deleted",
                        value=f"` - ` {log.user.mention} deleted __**`{log.extra.count}`**__ in {log.target.mention}\n` - ` Occured: {self.bot.timestamp(log.created_at, style='R')}",
                        inline=False)

                    if len(message_bulk_delete_emb.fields) > 3:
                        break
                    if len(message_bulk_delete_emb.fields) == 0:
                        message_bulk_delete_emb.description = f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nThere are no records of `deleting messages in bulk`."
                await interaction.followup.edit_message(embed=message_bulk_delete_emb, message_id=self.sent_message_id)
        except (NotFound, HTTPException):
            return

    # if self._select.select.values[0] == "misc"
    @discord.ui.button(label="Bot Add", style=discord.ButtonStyle.grey)
    async def bot_add(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            bot_add_emb = BaseEmbed(
                description=f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nIterating through the audit log takes time,\n please be patient once you've pressed a button",
                colour=0xff6464)
            bot_add_emb.set_footer(text=self.footer, icon_url=self.icon_url)

            async for log in self.ctx.guild.audit_logs(limit=None):
                if log.action is AuditLogAction.bot_add:
                    bot_add_emb.add_field(
                        name="Bot was Added",
                        value=f"` - ` {log.user.mention} added __**`{log.target}`**__\n` - ` Occured: {self.bot.timestamp(log.created_at, style='R')}",
                        inline=False)

                    if len(bot_add_emb.fields) > 3:
                        break
                    if len(bot_add_emb.fields) == 0:
                        bot_add_emb.description = f"\U0001f4dc **{self.ctx.guild}'s Audit Log**\n\nThere are no records of `adding a bot`."
                await interaction.followup.edit_message(embed=bot_add_emb, message_id=self.sent_message_id)
        except (NotFound, HTTPException):
            return

    async def on_timeout(self) -> None:
        try:
            for view in self.children:
                view.disabled = True
                view.style = discord.ButtonStyle.grey
            await self.message.edit(view=self)
        except (NotFound, HTTPException):
            return

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{self.ctx.clean_prefix}{self.ctx.command}` for the `{self.ctx.command}` command <:SarahPray:920484222421045258>"
        if interaction.user != self.ctx.author:
            try:
                return await interaction.response.send_message(content=f"{pain}", ephemeral=True)
            except (NotFound, HTTPException):
                return
        return True

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: Item[Any]) -> None:
        print(error)
