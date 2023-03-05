import asyncio
import time
from io import BytesIO
from typing import Dict, Optional, Union

import aiohttp
import discord
import humanize
from discord import app_commands
from discord.ext import commands

from ...bot import BaseBot
from ...context import BaseContext
from ...embed import BaseEmbed
from ...kernel.utilities.flags import user_badges, user_perms
from ...kernel.views.meta import PFP
from ...kernel.views.paginator import Paginator


class Discord(commands.Cog):
    """Commands related to Discord."""

    def __init__(self, bot: BaseBot):
        self.bot = bot
        self.delete: Dict = {}  # -------
        self.pre_edit: Dict = {}  # |-- > Snipe command related dictionaries
        self.post_edit: Dict = {}  # --=)

    @property
    def emote(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(
            name="Discord", id=930855436670889994, animated=True
        )

    # Listeners for "snipe" command
    # @commands.Cog.listener()
    # async def on_message_delete(self, message: discord.Message):
    #     query: str = "INSERT INTO snipe (guild_id, d_c_id, d_m_cc, d_m_a_id, d_m_ts) " \
    #                 "VALUES ($1, $2, $3, $4, $5)"
    #     if message.attachments:
    #         _query: str = "INSERT INTO snipe (guild_id, d_c_id, d_m_cc, d_m_a_id, d_m_ts, attachments) " \
    #                     "VALUES ($1, $2, $3, $4, $5, $6)"
    #         await self.bot.db.execute(query, message.guild.id, message.channel.id, message.content, message.author.id, message.created_at)
    #         __query: str = "UPDATE snipe " \
    #                     "SET attachments = $2 " \
    #                     "WHERE guild_id = $1 AND d_m_ts = $3"
    #         webhook_id: int = int(self.bot.config.get("SNIPE_ATTACHMENT_ID"))
    #         webhook_token: str = self.bot.config.get("SNIPE_ATTACHMENT_TOKEN")
    #         for file in message.attachments:
    #             async with aiohttp.ClientSession() as session:
    #                 webhook = discord.Webhook.partial(
    #                     id=webhook_id,
    #                     token=webhook_token,
    #                     session=session)
    #                 wbhk_sent_msg: discord.Message = await webhook.send(file=discord.File(BytesIO(file.read())), wait=True)
    #             await self.bot.db.execute(__query, message.guild.id, wbhk_sent_msg.attachments[0].url, message.created_at)

    #             await self.bot.db.execute()

    #     await self.bot.db.execute(query, message.guild.id, message.channel.id, message.content, message.author.id, message.created_at)

    @commands.Cog.listener()
    async def on_message_edit(
        self, pre_edit: discord.Message, post_edit: discord.Message
    ):
        self.pre_edit[pre_edit.channel.id] = (
            pre_edit.jump_url,
            pre_edit.content,
            pre_edit.author,
            pre_edit.channel.id,
            pre_edit.created_at,
        )
        self.post_edit[post_edit.channel.id] = (
            post_edit.content,
            post_edit.author,
            post_edit.channel.id,
            post_edit.edited_at,
        )

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

        # Latency with the database
        start_db = time.perf_counter()
        await self.bot.db.fetch("SELECT 1")
        end_db = time.perf_counter()
        db_ping = (end_db - start_db) * 1000

        # Latency for Discord Api
        websocket_ping = self.bot.latency * 1000

        ping_emb = BaseEmbed(title="__ My Latencies : __", colour=0x2F3136)

        if ctx.interaction:
            if ctx.author.is_on_mobile():
                ping_emb.description = f"""```yaml\n> PostgreSQL     : {round(db_ping, 1)} ms
> Discord API    : {websocket_ping:,.0f} ms\n```"""
                return await ctx.reply(
                    embed=ping_emb, mention_author=False, ephemeral=True
                )
            else:
                ping_emb.description = f"""```ansi\n\x1b[0;1;37;40m > \x1b[0m \x1b[0;1;34mPostgreSQL\x1b[0m     \x1b[0;1;37;40m : \x1b[0m \x1b[0;1;31m{round(db_ping, 1)} ms\x1b[0m
\x1b[0;1;37;40m > \x1b[0m \x1b[0;1;34mDiscord API\x1b[0m    \x1b[0;1;37;40m : \x1b[0m \x1b[0;1;31m{websocket_ping:,.0f} ms\x1b[0m\n```"""
                return await ctx.reply(
                    embed=ping_emb, mention_author=False, ephemeral=True
                )
        else:
            if ctx.author.is_on_mobile():
                ping_emb.description = f"""```yaml\n> PostgreSQL     : {round(db_ping, 1)} ms
> Discord API    : {websocket_ping:,.0f} ms
> Message Typing : {round(typing_ping, 1)} ms\n```"""
                return await ctx.reply(embed=ping_emb, mention_author=False)
            else:
                ping_emb.description = f"""```ansi\n\x1b[0;1;37;40m > \x1b[0m \x1b[0;1;34mPostgreSQL\x1b[0m     \x1b[0;1;37;40m : \x1b[0m \x1b[0;1;31m{round(db_ping, 1)} ms\x1b[0m
\x1b[0;1;37;40m > \x1b[0m \x1b[0;1;34mDiscord API\x1b[0m    \x1b[0;1;37;40m : \x1b[0m \x1b[0;1;31m{websocket_ping:,.0f} ms\x1b[0m
\x1b[0;1;37;40m > \x1b[0m \x1b[0;1;34mMessage Typing\x1b[0m \x1b[0;1;37;40m : \x1b[0m \x1b[0;1;31m{round(typing_ping, 1)} ms\x1b[0m\n```"""
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
        status = user.status
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
    async def snipe_delete(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Get the details of the recently deleted message"""
        try:
            message, author, channel, time = self.delete[ctx.channel.id]
            delete_emb = BaseEmbed(
                title="Sniped Deleted Message",
                description=f"**<:ReplyContinued:930634770004725821> - [Message Author :]({author.display_avatar.url})** {author.mention} (`{author.id}`)\n**<:ReplyContinued:930634770004725821> - In Channel :** <#{channel}> (`{channel}`)\n**<:Reply:930634822865547294> - Message Created At :** {self.bot.timestamp(time, style='R')}",
                colour=0x2F3136,
            )
            delete_emb.add_field(name="Message Content", value=f">>> {message}")
            await ctx.reply(embed=delete_emb, allowed_mentions=self.bot.mentions)
        except BaseException:
            await ctx.reply(
                "No one has deleted. any messages as of now <a:HumanBro:905748764432662549>",
                allowed_mentions=self.bot.mentions,
            )

    # Snipes for edited messages
    @snipe.command(
        name="edit",
        brief="Snipe Edited Messages",
        aliases=["ed", "e"],
        with_app_command=True,
    )
    @commands.cooldown(3, 5, commands.BucketType.user)
    async def snipe_edit(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Get the details of the recently edited message"""
        try:
            url, message, author, channel, pre_time = self.pre_edit[ctx.channel.id]
            post_message, author, channel, post_time = self.post_edit[ctx.channel.id]
            view = discord.ui.View()
            view.add_item(
                discord.ui.Button(
                    label="Jump to Message",
                    style=discord.ButtonStyle.link,
                    url=url,
                    emoji="<a:ChainLink:936158619030941706>",
                )
            )
            edit_emb = BaseEmbed(
                title="Sniped Edited Message",
                description=f"**<:ReplyContinued:930634770004725821> - [Message Author :]({author.display_avatar.url})** {author.mention} (`{author.id}`)\n**<:ReplyContinued:930634770004725821> - In Channel :** <#{channel}> (`{channel}`)\n**<:Reply:930634822865547294> - Message Sent At :** {self.bot.timestamp(pre_time, style='R')}",
                colour=0x2F3136,
            )
            edit_emb.add_field(name="Before Edit", value=f">>> {message}")
            edit_emb.add_field(
                name="After Edit",
                value=f"**<:Reply:930634822865547294> - Message Edited at :** {self.bot.timestamp(post_time, style='R')}\n>>> {post_message}",
                inline=False,
            )
            await ctx.reply(
                embed=edit_emb, allowed_mentions=self.bot.mentions, view=view
            )
        except BaseException:
            await ctx.reply(
                "No one has edited any messages as of now <a:BotLurk:905749164355379241>",
                allowed_mentions=self.bot.mentions,
            )
