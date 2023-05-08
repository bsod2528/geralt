import asyncio
import imghdr
import os
import textwrap
import time
from io import BytesIO
from typing import Dict, List, Optional, Union

import aiohttp
import discord
import humanize
from discord import app_commands
from discord.ext import commands, tasks

from ...bot import BaseBot
from ...context import BaseContext
from ...embed import BaseEmbed
from ...kernel.utilities.flags import user_badges, user_perms
from ...kernel.views.meta import PFP
from ...kernel.views.paginator import Paginator
from ...kernel.views.snipe import (
    EditSnipeAttachmentView,
    SnipeAttachmentViewer,
    SnipeStats,
)

escape: str = "\x1b"


class Discord(commands.Cog):
    """Commands related to Discord."""

    def __init__(self, bot: BaseBot):
        self.bot = bot
        self.pic_exts = ["png", "jpg", "jpeg", "gif", "bmp", "tiff", "svg"]

    @property
    def emote(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(
            name="Discord", id=930855436670889994, animated=True
        )

    @tasks.loop(minutes=10)
    async def snipe_purge(self):
        self.bot.settings.items()

    def return_ext(self, file: discord.File) -> str:
        filename, ext = os.path.splitext(file.filename)
        return ext.lower()[1:] if ext else ""

    def colorize(self, value: int, thresholds: Dict[int, int]) -> str:
        for threshold, color in thresholds.items():
            if value <= threshold:
                return f"{escape}[0;1;{color}m{value} ms{escape}[0m"

    # Listeners for "snipe" command
    @commands.Cog.listener("on_message")
    async def on_message(self, message: discord.Message):
        if message.guild is not None:
            try:
                log = self.bot.settings[message.guild.id]["snipe"]
            except KeyError:
                log = await self.bot.db.fetch(
                    "SELECT snipe FROM guild_settings WHERE guild_id = $1",
                    message.guild.id,
                )
            if log == True:
                self.bot.snipe_counter[message.guild.id]["total_messages"] += 1

    @commands.Cog.listener("on_message_delete")
    async def on_message_delete(self, message: discord.Message):
        if message.guild is not None:
            try:
                log = self.bot.settings[message.guild.id]["snipe"]
            except KeyError:
                log = await self.bot.db.fetch(
                    "SELECT snipe FROM guild_settings WHERE guild_id = $1",
                    message.guild.id,
                )
                # don't be a bitch about my column names :moyai:

                if log == True:
                    if message.author.bot:
                        return
                    embeds: List[BaseEmbed] = []
                    attachment_exts: List[str] = []
                    attachment_urls: List[str] = []
                    attachment_names: List[str] = []
                    attachment_bytes: List[bytes] = []
                    if message.attachments:
                        for file in message.attachments:
                            ext = self.return_ext(file)
                            if ext in self.pic_exts:
                                ext = imghdr.what(BytesIO(await file.read()))
                            attachment_exts.append(ext)
                            attachment_names.append(file.filename)
                            attachment_bytes.append(await file.read())

                    if len(attachment_names) >= 2:
                        attachment_bytes.clear()
                        for attachment in message.attachments:
                            async with aiohttp.ClientSession() as session:
                                wbhk = discord.Webhook.partial(
                                    id=self.bot.config.get("SNIPE_ATTACHMENT_ID"),
                                    token=self.bot.config.get("SNIPE_ATTACHMENT_TOKEN"),
                                    session=session,
                                )
                                _attachment = await attachment.read()
                                sent_attachment_message = await wbhk.send(
                                    file=discord.File(
                                        BytesIO(_attachment),
                                        filename=attachment.filename,
                                    ),
                                    wait=True,
                                )
                                attachment_urls.append(
                                    sent_attachment_message.attachments[0].url
                                )

                    if message.embeds:
                        for embed in message.embeds:
                            embeds.append(embed.to_dict())

                    query = """
                    INSERT INTO snipe_delete
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        """

                    await self.bot.db.execute(
                        query,
                        message.guild.id,
                        message.channel.id,
                        message.author.id,
                        message.content,
                        message.created_at,
                        embeds,
                        attachment_names,
                        attachment_bytes,
                        attachment_urls,
                        attachment_exts,
                    )
                    try:
                        self.bot.snipe_counter[message.guild.id]["delete"] += 1
                    except:
                        return

    @commands.Cog.listener("on_message_edit")
    async def on_message_edit(self, pre: discord.Message, post: discord.Message):
        if pre.guild is not None:
            try:
                log = self.bot.settings[pre.guild.id]["snipe"]
            except KeyError:
                log = await self.bot.db.fetch(
                    "SELECT snipe FROM guild_settings WHERE guild_id = $1",
                    pre.guild.id,
                )

            if log == True:
                if pre.author.bot and post.author.bot:
                    return
                pre_attachment_exts: List[str] = []
                pre_attachment_urls: List[str] = []
                pre_attachment_names: List[str] = []
                pre_attachment_bytes: List[bytes] = []

                post_attachment_exts: List[str] = []
                post_attachment_urls: List[str] = []
                post_attachment_names: List[str] = []
                post_attachment_bytes: List[bytes] = []

                if pre.attachments:
                    for file in pre.attachments:
                        ext = self.return_ext(file)
                        if ext in self.pic_exts:
                            ext = imghdr.what(BytesIO(await file.read()))
                        pre_attachment_exts.append(ext)
                        pre_attachment_names.append(file.filename)
                        pre_attachment_bytes.append(await file.read())

                if len([pre_attachment_names]) >= 2:
                    for attachment in pre.attachments:
                        async with aiohttp.ClientSession() as session:
                            wbhk = discord.Webhook.partial(
                                id=self.bot.config.get("SNIPE_ATTACHMENT_ID"),
                                token=self.bot.config.get("SNIPE_ATTACHMENT_TOKEN"),
                                session=session,
                            )

                            _attachment = await attachment.read()
                            sent_attachment_message = await wbhk.send(
                                file=discord.File(
                                    BytesIO(_attachment), filename=attachment.filename
                                ),
                                wait=True,
                            )
                            pre_attachment_urls.append(
                                sent_attachment_message.attachments[0].url
                            )

                if post.attachments:
                    for _file in post.attachments:
                        ext = self.return_ext(_file)
                        if ext in self.pic_exts:
                            ext = imghdr.what(BytesIO(await _file.read()))
                        post_attachment_exts.append(ext)
                        post_attachment_names.append(_file.filename)
                        post_attachment_bytes.append(await _file.read())

                if len([post_attachment_names]) >= 2:
                    for _attachment in post.attachments:
                        async with aiohttp.ClientSession() as session:
                            wbhk = discord.Webhook.partial(
                                id=self.bot.config.get("SNIPE_ATTACHMENT_ID"),
                                token=self.bot.config.get("SNIPE_ATTACHMENT_TOKEN"),
                                session=session,
                            )

                            __attachment = await attachment.read()
                            _sent_attachment_message = await wbhk.send(
                                file=discord.File(
                                    BytesIO(__attachment), filename=_attachment.filename
                                ),
                                wait=True,
                            )
                            pre_attachment_urls.append(
                                _sent_attachment_message.attachments[0].url
                            )

                query: str = """
                INSERT INTO snipe_edit
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)"""

                await self.bot.db.execute(
                    query,
                    pre.guild.id,
                    pre.channel.id,
                    pre.id,
                    pre.author.id,
                    pre.content,
                    pre.created_at,
                    post.content,
                    post.created_at,
                    pre_attachment_exts,
                    pre_attachment_urls,
                    pre_attachment_names,
                    pre_attachment_bytes,
                    post_attachment_names,
                    post_attachment_urls,
                    post_attachment_names,
                    post_attachment_bytes,
                    post.jump_url,
                )
                try:
                    self.bot.snipe_counter[post.guild.id]["edit"] += 1
                except:
                    return

    @commands.hybrid_command(name="ping", brief="You ping Me", aliases=["pong"])
    @app_commands.checks.cooldown(2, 10)
    @commands.cooldown(2, 10, commands.BucketType.user)
    async def ping(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Get proper latency timings of the bot."""

        # Latency for typing
        typing_start = time.perf_counter()
        async with ctx.typing():
            await asyncio.sleep(0.5)
        typing_end = time.perf_counter()
        typing_ping = (typing_end - typing_start) * 1000
        typing_ping = round(typing_ping, 1)

        # Latency with the database
        start_db = time.perf_counter()
        await self.bot.db.fetch("SELECT 1")
        end_db = time.perf_counter()
        db_ping = round((end_db - start_db) * 1000, 1)

        # Latency for Discord Api
        websocket_ping = round(self.bot.latency * 1000, 0)

        mob_type_ping = typing_ping
        mob_db_ping = db_ping
        mob_wb_ping = websocket_ping

        typing_threshold: Dict[int, int] = {900: 32, 1000: 33, 1500: 31}

        db_thresholds: Dict[int, int] = {5: 32, 15: 33, 20: 31}

        websocket_thresholds: Dict[int, int] = {
            350: 32,
            450: 33,
            500: 31,
        }
        typing_ping = self.colorize(typing_ping, typing_threshold)
        db_ping = self.colorize(db_ping, db_thresholds)
        websocket_ping = self.colorize(websocket_ping, websocket_thresholds)

        ping_emb = BaseEmbed(title="__ My Latencies : __", colour=0x2F3136)

        if ctx.interaction:
            if ctx.author.is_on_mobile():
                ping_emb.description = f"""```yaml\n> PostgreSQL     : {mob_db_ping}
> Discord API    : {mob_wb_ping}\n```"""
                return await ctx.reply(
                    embed=ping_emb, mention_author=False, ephemeral=True
                )
            else:
                ping_emb.description = f"""```ansi\n{escape}[0;1;37;40m > {escape}[0m {escape}[0;1;34mPostgreSQL{escape}[0m     {escape}[0;1;37;40m : {escape}[0m {db_ping}{escape}[0m
{escape}[0;1;37;40m > {escape}[0m {escape}[0;1;34mDiscord API{escape}[0m    {escape}[0;1;37;40m : {escape}[0m {escape}[0;1;31m{websocket_ping} {escape}[0m\n```"""
                return await ctx.reply(
                    embed=ping_emb, mention_author=False, ephemeral=True
                )
        else:
            if ctx.author.is_on_mobile():
                ping_emb.description = f"""```yaml\n> PostgreSQL     : {mob_db_ping} ms
> Discord API    : {mob_wb_ping} ms
> Message Typing : {mob_type_ping} ms\n```"""
                return await ctx.reply(embed=ping_emb, mention_author=False)
            else:
                ping_emb.description = f"""```ansi\n{escape}[0;1;37;40m > {escape}[0m {escape}[0;1;34mPostgreSQL{escape}[0m     {escape}[0;1;37;40m : {escape}[0m {escape}[0;1;31m{db_ping}{escape}[0m
{escape}[0;1;37;40m > {escape}[0m {escape}[0;1;34mDiscord API{escape}[0m    {escape}[0;1;37;40m : {escape}[0m {escape}[0;1;31m{websocket_ping}{escape}[0m
{escape}[0;1;37;40m > {escape}[0m {escape}[0;1;34mMessage Typing{escape}[0m {escape}[0;1;37;40m : {escape}[0m {escape}[0;1;31m{typing_ping}{escape}[0m\n```"""
            return await ctx.reply(embed=ping_emb, mention_author=False)

    @commands.command(name="banner", brief="View a persons banner")
    async def banner(
        self, ctx: BaseContext, *, user: Union[discord.Member, discord.User] = None
    ) -> Optional[discord.Message]:
        """See the user's Banner in an enlarged manner."""
        user = user or ctx.author
        if ctx.message.reference:
            user = ctx.message.reference.resolved.author
        fetched_user = await ctx.bot.fetch_user(user.id)
        if fetched_user.banner is None:
            return await ctx.reply(
                f"**{user}** does not have a banner <a:Grimacing:914905757588283422>"
            )
        banner_emb = BaseEmbed(
            title=f"{user}'s Banner",
            colour=user.colour or user.accent_color or self.bot.colour,
        )
        banner_emb.set_image(url=fetched_user.banner.url)
        await ctx.reply(embed=banner_emb, mention_author=False)

    # Get user's PFP
    @commands.command(
        name="avatar", brief="View a persons PFP", aliases=["pfp", "pp", "dp", "av"]
    )
    async def avatar(
        self, ctx: BaseContext, *, user: Union[discord.User, discord.Member] = None
    ) -> Optional[discord.Message]:
        """See the user's PFP in an enlarged manner."""
        user = user or ctx.author
        if ctx.message.reference:
            user = ctx.message.reference.resolved.author
            return await PFP(self.bot, ctx, user).send()
        if user == ctx.author:
            log_avatar = await self.bot.db.fetchval(
                "SELECT avatar FROM user_settings WHERE user_id = $1", ctx.author.id
            )
            if not log_avatar:
                no_avatar_log_user = PFP(self.bot, ctx, ctx.author)
                no_avatar_log_user.save.disabled = True
                return await no_avatar_log_user.send()
            if log_avatar:
                avatar_log_user = PFP(self.bot, ctx, ctx.author)
                return await avatar_log_user.send()
        await PFP(self.bot, ctx, user).send()

    # Get user's information
    @commands.hybrid_command(
        name="userinfo",
        brief="Get user information",
        aliases=["user", "ui"],
        with_app_command=True,
    )
    @commands.guild_only()
    async def userinfo(
        self, ctx: BaseContext, *, user: discord.Member = None
    ) -> Optional[discord.Message]:
        """Get entire details about a user."""
        user = user or ctx.author
        if ctx.message.reference:
            user = ctx.message.reference.resolved.author
        roles = ""
        for role in user.roles:
            if role is ctx.guild.default_role:
                continue
            roles = f"{roles} {role.mention}"
        if roles != "":
            roles = f"{roles}"
        fetched_user = await ctx.bot.fetch_user(user.id)
        permissions = user_perms(user.guild_permissions)
        if permissions:
            perms_ = f"{' **|** '}".join(permissions)
        avatar = user.display_avatar.with_static_format("png")
        status = str(user.status).capitalize()
        colour: discord.colour.Colour = user.colour
        if colour == discord.Colour.from_rgb(0, 0, 0):
            colour = 0x2F3136

        general_emb = BaseEmbed(title=f":scroll: {user}'s Information", colour=colour)
        general_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> General Info :",
            value=f"> <:ReplyContinued:930634770004725821> Name: {user.mention} \n"
            f"> <:ReplyContinued:930634770004725821> Nickname: {(user.nick) or 'No nickname set'} \n"
            f"> <:ReplyContinued:930634770004725821> Discriminator: `#{user.discriminator}` \n"
            f"> <:Reply:930634822865547294> Identification No.: `{user.id}` \n────",
        )
        general_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Account Info:",
            value=f"> <:ReplyContinued:930634770004725821> Join Position: `#{sorted(ctx.guild.members, key = lambda u: u.joined_at or discord.utils.utcnow()).index(user) + 1}`\n "
            f"> <:ReplyContinued:930634770004725821> Created on: {self.bot.timestamp(user.created_at, style = 'd')} ({self.bot.timestamp(user.created_at, style = 'R')}) \n"
            f"> <:Reply:930634822865547294> Joined Guild on: {self.bot.timestamp(user.joined_at, style = 'd')} ({self.bot.timestamp(user.joined_at, style = 'R')})\n────",
            inline=False,
        )
        general_emb.set_thumbnail(url=avatar)

        guild_emb = BaseEmbed(title=f":scroll: {user} in {ctx.guild}", colour=colour)
        guild_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Permissions Present:",
            value=f"> <:Reply:930634822865547294> {perms_}\n────",
        )
        guild_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Top Most Role:",
            value=f"> <:Reply:930634822865547294> {user.top_role.mention}\n────",
            inline=False,
        )
        guild_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> All Roles Present:",
            value=f"> <:Reply:930634822865547294> {roles}\n────",
            inline=False,
        )
        guild_emb.set_thumbnail(url=avatar)

        misc_emb = BaseEmbed(
            title=f":scroll: {user}'s - Misc. Information", colour=colour
        )
        misc_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Badges Present:",
            value=f"> <:Reply:930634822865547294> {user_badges(user=user) if user_badges(user=user) else 'No Badges Present'}",
        )
        misc_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Accent Colours:",
            value=f"> <:ReplyContinued:930634770004725821> Banner Colour: `{str(fetched_user.accent_colour).upper()}` \n"
            f"> <:Reply:930634822865547294> Guild Role Colour: `{user.color if user.color is not discord.Color.default() else 'Default'}`\n────",
            inline=False,
        )
        misc_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Custom Status:",
            value=f"> <:Reply:930634822865547294> {status}",
            inline=False,
        )
        misc_emb.set_thumbnail(url=avatar)

        pfp_emb = BaseEmbed(
            title=f":scroll: {user}'s PFP",
            description=f"[**JPG Format**]({user.display_avatar.with_static_format('jpg')}) │ [**PNG Format**]({user.display_avatar.with_static_format('png')}) │ [**WEBP Format**]({user.display_avatar.with_static_format('webp')})",
            colour=colour,
        )
        pfp_emb.set_image(url=avatar)

        banner_emb = None

        if fetched_user.banner is None:
            embed_list = [general_emb, guild_emb, misc_emb, pfp_emb]
            async with ctx.channel.typing():
                await asyncio.sleep(0.1)
            await Paginator(self.bot, ctx, embeds=embed_list).send(ctx)
        else:
            banner_emb = BaseEmbed(
                title=f":scroll: {user}'s Banner",
                description=f"[**Download Banner Here**]({fetched_user.banner.url})",
                colour=colour,
            )
            banner_emb.set_image(url=fetched_user.banner.url)

            embed_list = [general_emb, guild_emb, misc_emb, pfp_emb, banner_emb]
            async with ctx.channel.typing():
                await asyncio.sleep(0.1)
            await Paginator(self.bot, ctx, embeds=embed_list).send(ctx)

    @commands.hybrid_command(
        name="serverinfo",
        brief="Get guild information",
        aliases=["si", "gi"],
        with_app_command=True,
    )
    @commands.guild_only()
    async def server_info(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Get entire details about the guild."""
        user_status = [
            len(list(filter(lambda u: str(u.status) == "online", ctx.guild.members))),
            len(list(filter(lambda u: str(u.status) == "idle", ctx.guild.members))),
            len(list(filter(lambda u: str(u.status) == "dnd", ctx.guild.members))),
            len(list(filter(lambda u: str(u.status) == "offline", ctx.guild.members))),
        ]
        fetched_guild = await ctx.bot.fetch_guild(ctx.guild.id)

        general_emb = BaseEmbed(
            title=f":scroll: {ctx.guild.name}'s Information", colour=self.bot.colour
        )
        general_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> General Information :",
            value=f"> <:ReplyContinued:930634770004725821> <a:WumpusHypesquad:905661121501990923> Owner: {ctx.guild.owner.mention} (`{ctx.guild.owner.id}`) \n"
            f"> <:ReplyContinued:930634770004725821> <a:Users:905749451350638652> No. of Roles: `{len(ctx.guild.roles)}` \n"
            f"> <:ReplyContinued:930634770004725821> <a:Info:905750331789561856> Identification No.: `{ctx.guild.id}` \n"
            f"> <:ReplyContinued:930634770004725821> <a:Verify:905748402871095336> Verification Level: {str(ctx.guild.verification_level).replace('_', ' ').replace('`NONE`', '`NILL`').title()} \n"
            f"> <:Reply:930634822865547294> <:WinFileBruh:898571301986373692> File Transfer Limit: `{humanize.naturalsize(ctx.guild.filesize_limit)}`\n────",
        )
        general_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Initialisation :",
            value=f"> <:ReplyContinued:930634770004725821> <a:Woo:905754435379163176> Made On: {self.bot.timestamp(ctx.guild.created_at, style='d')} \n"
            f"> <:Reply:930634822865547294> <:ISus:915817563307515924> Media Filteration: For `{str(ctx.guild.explicit_content_filter).replace('_',' ').replace('`NONE`', '`NILL`').title()}` \n────",
            inline=False,
        )
        general_emb.set_thumbnail(url=ctx.guild.icon.url)

        other_emb = BaseEmbed(
            title=f":scroll: {ctx.guild.name}'s Other Information",
            colour=self.bot.colour,
        )
        other_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Channel Information:",
            value=f"> <:ReplyContinued:930634770004725821> <:Channel:905674680436944906> Text: `{len(ctx.guild.text_channels)}` \n"
            f"> <:ReplyContinued:930634770004725821> <:Voice:905746719034187796> Voice: `{len(ctx.guild.voice_channels)}` \n"
            f"> <:ReplyContinued:930634770004725821> <a:Thread:905750997706629130> Threads: `{len(ctx.guild.threads)}` \n"
            f"> <:Reply:930634822865547294> <:StageChannel:905674422839554108> Stage: `{len(ctx.guild.stage_channels)}` \n────",
            inline=False,
        )
        other_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Emotes Present:",
            value=f"> <:ReplyContinued:930634770004725821> <a:IThink:933315875501641739> Animated: `{len([animated for animated in ctx.guild.emojis if animated.animated])}` / `{ctx.guild.emoji_limit}` \n"
            f"> <:Reply:930634822865547294> <:BallManHmm:933398958263386222> Non - Animated: `{len([non_animated for non_animated in ctx.guild.emojis if not non_animated.animated])}` / `{ctx.guild.emoji_limit}`\n────",
            inline=False,
        )
        other_emb.set_thumbnail(url=ctx.guild.icon.url)

        user_emb = BaseEmbed(
            title=f":scroll: {ctx.guild.name}'s Users Information",
            colour=self.bot.colour,
        )
        user_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> No. of Users:",
            value=f"> <:ReplyContinued:930634770004725821> <a:HumanBro:905748764432662549> No. of Humans: `{len(list(filter(lambda u : u.bot is False, ctx.guild.members)))}` \n"
            f"> <:ReplyContinued:930634770004725821> <a:BotLurk:905749164355379241> No. of Bots: `{len(list(filter(lambda u : u.bot, ctx.guild.members)))}` \n"
            f"> <:Reply:930634822865547294> <a:Users:905749451350638652> Total: `{ctx.guild.member_count}`\n────",
            inline=False,
        )
        user_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Activity Information:",
            value=f"> <:ReplyContinued:930634770004725821> <:Online:905757053119766528> Online: `{user_status[0]}` \n"
            f"> <:ReplyContinued:930634770004725821> <:Idle:905757063064453130> Idle: `{user_status[1]}` \n"
            f"> <:ReplyContinued:930634770004725821> <:DnD:905759353141874709> Do Not Disturb: `{user_status[2]}` \n"
            f"> <:Reply:930634822865547294> <:Offline:905757032521551892> Offline: `{user_status[3]}`\n────",
            inline=False,
        )
        user_emb.set_thumbnail(url=ctx.guild.icon.url)

        icon_emb = BaseEmbed(
            title=f":scroll: {ctx.guild.name}'s Icon",
            description=f"[**JPG Format**]({ctx.guild.icon.with_static_format('jpg')}) │ [**PNG Format**]({ctx.guild.icon.with_static_format('png')}) │ [**WEBP Format**]({ctx.guild.icon.with_static_format ('webp')})",
            colour=self.bot.colour,
        )
        icon_emb.set_image(url=ctx.guild.icon.url)

        banner_emb = None

        if fetched_guild.banner is None:
            embed_list = [general_emb, other_emb, user_emb, icon_emb]
            async with ctx.channel.typing():
                await asyncio.sleep(0.1)
            await Paginator(self.bot, ctx, embeds=embed_list).send(ctx)
        else:
            banner_emb = BaseEmbed(
                title=f":scroll: {ctx.guild.name}'s Banner",
                description=f"[**Download Banner Here**]({fetched_guild.banner.url})",
                colour=self.bot.colour,
            )
            banner_emb.set_image(url=fetched_guild.banner.url)

            embed_list = [general_emb, other_emb, user_emb, icon_emb, banner_emb]
            async with ctx.channel.typing():
                await asyncio.sleep(0.1)
            await Paginator(self.bot, ctx, embeds=embed_list).send(ctx)

    @commands.command(name="spotify", brief="Get Spotify Info.", aliases=["sp", "spot"])
    async def spotify(
        self, ctx: BaseContext, *, user: Union[discord.Member, discord.User] = None
    ) -> Optional[discord.Message]:
        """Get Information on what the user is listening to."""
        user = user or ctx.author
        view = discord.ui.View()
        try:
            spotify = discord.utils.find(
                lambda sp: isinstance(sp, discord.Spotify), user.activities
            )
        except BaseException:
            return await ctx.reply(f"`{user}` is not in this guild, I'm sorry.")
        if spotify is None:
            if user == ctx.author:
                return await ctx.reply("You are not listening to Spotify right now.")
            else:
                return await ctx.reply(
                    f"**{user}** is not listening to any song on **Spotify** right now."
                )
        else:
            spotify_emb = BaseEmbed(
                title=f":scroll: {user}'s Spotify Status",
                description=f"They are listening to [**{spotify.title}**]({spotify.track_url}) by - **{spotify.artist}**",
                colour=self.bot.colour,
            )
            spotify_emb.add_field(
                name="Song Information :",
                value=f"> <:ReplyContinued:930634770004725821> ` - ` **Name :** [**{spotify.title}**]({spotify.track_url})\n"
                f"> <:ReplyContinued:930634770004725821> ` - ` **Album :** {spotify.album}\n"
                f"> <:Reply:930634822865547294> ` - ` **Duration :** {humanize.precisedelta(spotify.duration)}",
            )
            spotify_emb.set_thumbnail(url=spotify.album_cover_url)
            view.add_item(
                discord.ui.Button(
                    label="Listen on Spotify",
                    url=spotify.track_url,
                    emoji="<a:Spotify:993120872883834990>",
                )
            )
            await ctx.reply(embed=spotify_emb, mention_author=False, view=view)

    # Snipe command as a group
    # TODO: Finish :meth: ~ snipe_edit(). Too lazy
    @commands.hybrid_group(name="snipe", aliases=["s"], with_app_command=True)
    @commands.cooldown(3, 5, commands.BucketType.user)
    @commands.guild_only()
    async def snipe(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Get edited / deleted messages"""
        if ctx.invoked_subcommand is None:
            await ctx.command_help()

    # Snipes for deleted messages
    @snipe.command(
        name="delete",
        brief="Snipe Deleted Messages",
        aliases=["del", "d"],
        with_app_command=True,
    )
    @commands.cooldown(3, 5, commands.BucketType.user)
    @app_commands.describe(
        index="The order at which you want to snipe.",
        channel="The text-channel do you want to snipe.",
        user="Filter sniped messages according to a user.",
    )
    async def snipe_delete(
        self,
        ctx: BaseContext,
        index: Optional[int],
        channel: Optional[discord.TextChannel],
        user: Optional[Union[discord.User, discord.Member]],
    ) -> Optional[discord.Message]:
        """Sends details on recently deleted message."""

        if not index:
            index = 0
        if not channel:
            channel = ctx.channel
        if not user:
            query: str = f"SELECT * FROM snipe_delete WHERE guild_id = $1 AND d_m_c_id = $2 ORDER BY d_m_ts DESC OFFSET {index} LIMIT 1"
            snipe_records = await self.bot.db.fetch(query, ctx.guild.id, channel.id)
        else:
            query: str = f"SELECT * FROM snipe_delete WHERE guild_id = $1 AND d_m_a_id = $2 AND d_m_c_id = $3 ORDER BY d_m_ts DESC OFFSET {index} LIMIT 1"
            snipe_records = await self.bot.db.fetch(
                query, ctx.guild.id, user.id, channel.id
            )
        if not snipe_records:
            return await ctx.send(
                f"**{ctx.guild}** - has no snipes recorded in {channel.mention} <a:IWait:948253556190904371>"
            )

        _embed: BaseEmbed = None

        for record in snipe_records:
            user = ctx.guild.get_member(record[2])
            _time = discord.utils.utcnow() - record[4]

            snipe_embed = BaseEmbed(
                description=record[3] if record[3] else "_No content was present._",
                color=self.bot.colour,
            )
            snipe_embed.set_author(
                name=f"{user} said in {ctx.guild.get_channel(record[1])} ...",
                icon_url=user.display_avatar.url,
            )
            snipe_embed.set_footer(text=f"Deleted {humanize.precisedelta(_time)} ago")

            file = record[7][0] if record[7] else None
            file_urls: List[str] = [url for url in record[8] if record[8] >= 2]
            embeds: List[BaseEmbed] = [snipe_embed]

            if record[5]:
                for _dict in record[5]:
                    embeds.append(BaseEmbed().from_dict(dict(_dict)))

            try:
                for z in record[6]:
                    if z.split(".")[-1] in self.pic_exts:
                        snipe_embed.set_image(url=file_urls[0])
            except IndexError:
                pass

            serial_no: int = 1
            for x in file_urls:
                if x.split(".")[-1] in self.pic_exts:
                    if x == snipe_embed.image.url:
                        continue
                    embed = snipe_embed.copy()
                    embed.set_image(url=x)
                    embeds.append(embed)
                else:
                    snipe_embed.add_field(
                        name="Urls for Attachments",
                        value=f"[Attachment {serial_no}]({x})",
                        inline=False,
                    )
                    serial_no += 1

            if file_urls:
                for gamma in file_urls:
                    if gamma.split(".")[-1] in self.pic_exts:
                        return await Paginator(self.bot, ctx, embeds).send(ctx)
                else:
                    await ctx.send(embed=snipe_embed)
            elif file:
                if index == 0:
                    if len(embeds) == 1:
                        view = SnipeAttachmentViewer(
                            ctx, file_data=file, filename=record[6][0]
                        )
                        view.message = await ctx.send(embeds=embeds, view=view)
                        return
                    view = SnipeAttachmentViewer(
                        ctx, file_data=file, filename=record[6][0]
                    )
                    view.message = await ctx.send(embeds=embeds, view=view)
                else:
                    if len(embeds) == 1:
                        view = SnipeAttachmentViewer(
                            ctx, embeds=embeds, file_data=file, filename=record[6][0]
                        )
                        view.message = await ctx.send(embeds=embeds, view=view)
                        return
                    view = SnipeAttachmentViewer(
                        ctx, file_data=file, filename=record[6][0]
                    )
                    view.message = await ctx.send(embeds=embeds, view=view)
            else:
                if index == 0:
                    if len(embeds) == 1:
                        await ctx.send(embed=snipe_embed)
                    else:
                        await ctx.send(embeds=embeds)
                else:
                    if len(embeds) == 1:
                        await ctx.send(embed=snipe_embed)
                    else:
                        await ctx.send(embeds=embeds)

    # Snipes for edited messages
    @snipe.command(
        name="edit",
        brief="Snipe Edited Messages",
        aliases=["ed", "e"],
        with_app_command=True,
    )
    @commands.cooldown(3, 5, commands.BucketType.user)
    @app_commands.describe(
        channel="The text-channel do you want to snipe.",
        user="Filter sniped messages according to a user.",
        index="The order at which you want to snipe.",
    )
    async def snipe_edit(
        self,
        ctx: BaseContext,
        channel: Optional[discord.TextChannel],
        user: Optional[Union[discord.Member, discord.User]],
        index: Optional[int] = 0,
    ) -> Optional[discord.Message]:
        """Get the details of the recently edited message"""

        if not channel:
            channel = ctx.channel

        if not user:
            query: str = f"SELECT * FROM snipe_edit WHERE guild_id = $1 AND pre_c_id = $2 ORDER BY post_ts DESC OFFSET {index} LIMIT 1"
            snipe_records = await self.bot.db.fetch(query, ctx.guild.id, channel.id)
            if not snipe_records:
                return await ctx.send(
                    f"**{ctx.guild}** - has no snipes recorded in {channel.mention} <a:IWait:948253556190904371>"
                )
        else:
            query: str = f"SELECT * FROM snipe_edit WHERE guild_id = $1 AND pre_c_id = $2 AND pre_m_a_id = $3 ORDER BY post_ts DESC OFFSET {index} LIMIT 1"
            snipe_records = await self.bot.db.fetch(
                query, ctx.guild.id, channel.id, user.id
            )
            if not snipe_records:
                return await ctx.send(
                    f"**{ctx.guild}** - has no snipes recorded in {channel.mention} for {user.mention} <a:IWait:948253556190904371>",
                    allowed_mentions=self.bot.allowed_mentions,
                )

        _embed: BaseEmbed = None

        for record in snipe_records:
            user = ctx.guild.get_member(record[3])
            _time = discord.utils.utcnow() - record[7]

            description: str = f"""
            **Before Edit:**
            {record[4] if record[4] else '_No content was present._'}

            **After Edit:**
            {record[6] if record[6] else '_No content was present._'}"""
            snipe_embed = BaseEmbed(
                description=description,
                colour=self.bot.colour,
            )
            snipe_embed.set_author(
                icon_url=user.display_avatar.url,
                name=f"{user} edited in {ctx.guild.get_channel(record[1])}",
            )
            view = discord.ui.View()
            view.add_item(
                discord.ui.Button(
                    label="Jump Url",
                    style=discord.ButtonStyle.grey,
                    emoji="<a:ChainLink:936158619030941706>",
                    url=record[16],
                )
            )
            snipe_embed.set_footer(text=f"Edited {humanize.precisedelta(_time)}")

            # pre_file_names: List[str] = record[10] or []
            # pre_file_bytes: List[bytes] = record[1] or []

            # post_file_names: List[str] = record[14] or []
            # post_file_bytes: List[bytes] = record[15] or []

            # if record[10]:
            #     for name in record[10]:
            #         pre_file_names.append(name)

            # if post_file_bytes:
            #     view = EditSnipeAttachmentView(
            #         ctx,
            #         pre_file_bytes,
            #         post_file_bytes,
            #     )
            #     view.message = await ctx.send(embed=snipe_embed,view=view)
            #     return

        await ctx.send(embed=snipe_embed, view=view)

    @snipe.command(name="stats", brief="Stats on snipe", with_app_command=True)
    async def snipe_stats(self, ctx: BaseContext, flag: Optional[SnipeStats]):
        """Get guild and global snipe stats
        ────
        **Flags Present:**
        `--globalstats`: Sends global stats for snipe.
        <:Join:932976724235395072> **Arg Needed**: `True` or `False`
        **Example:**
        `.gsnipe stats [--globalstats True]`
        """
        time = discord.utils.utcnow() - self.bot.uptime
        if not flag:
            counter = self.bot.snipe_counter[ctx.guild.id]
            description: str = f"Stats from: {humanize.precisedelta(time)}\n<:ReplyContinued:930634770004725821> **Deleted:** `{counter['delete']}` message{'s' if counter['delete'] != 1 else ''}\n<:ReplyContinued:930634770004725821> **Edited:** `{counter['edit']}` message{'s' if counter['edit'] != 1 else ''}\n<:Reply:930634822865547294> **Total Messages:** `{counter['total_messages']}` message{'s' if counter['total_messages'] != 1 else ''}"
            stats_emb = BaseEmbed(
                title=f"Snipe Stats in {ctx.guild}",
                description=textwrap.dedent(description),
                colour=self.bot.colour,
            )
            stats_emb.set_footer(
                icon_url=ctx.author.display_avatar.url, text=f"Invoked By: {ctx.author}"
            )
            return await ctx.send(embed=stats_emb)
