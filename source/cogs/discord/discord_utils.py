import time
import asyncio
import discord
import humanize

from discord.ext import commands
from discord import app_commands
from typing import Union, Optional

from ...kernel.views.meta import PFP
from ...kernel.subclasses.bot import Geralt
from ...kernel.views.paginator import Paginator
from ...kernel.subclasses.embed import BaseEmbed
from ...kernel.subclasses.context import GeraltContext
from ...kernel.utilities.flags import user_badges, user_perms


class Discord(commands.Cog):
    """Commands related to Discord."""

    def __init__(self, bot: Geralt):
        self.bot: Geralt = bot

    @property
    def emote(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(
            name="Discord",
            id=930855436670889994,
            animated=True)

    @commands.hybrid_command(
        name="ping",
        brief="You ping Me",
        aliases=["pong"])
    @app_commands.checks.cooldown(2, 10)
    @commands.cooldown(2, 10, commands.BucketType.user)
    async def ping(self, ctx: GeraltContext) -> Optional[discord.Message]:
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

        ping_emb = BaseEmbed(
            title="__ My Latencies : __",
            colour=0x2F3136)

        if ctx.interaction:
            if ctx.author.is_on_mobile():
                ping_emb.description = f"""```yaml\n> PostgreSQL     : {round(db_ping, 1)} ms
> Discord API    : {websocket_ping:,.0f} ms\n```"""
                return await ctx.reply(embed=ping_emb, mention_author=False, ephemeral=True)
            else:
                ping_emb.description = f"""```ansi\n\x1b[0;1;37;40m > \x1b[0m \x1b[0;1;34mPostgreSQL\x1b[0m     \x1b[0;1;37;40m : \x1b[0m \x1b[0;1;31m{round(db_ping, 1)} ms\x1b[0m
\x1b[0;1;37;40m > \x1b[0m \x1b[0;1;34mDiscord API\x1b[0m    \x1b[0;1;37;40m : \x1b[0m \x1b[0;1;31m{websocket_ping:,.0f} ms\x1b[0m\n```"""
                return await ctx.reply(embed=ping_emb, mention_author=False, ephemeral=True)
        else:
            if ctx.author.is_on_mobile():
                ping_emb.description = f"""```yaml\n> PostgreSQL     : {round(db_ping, 1)} ms
> Discord API    : {websocket_ping:,.0f} ms
> Message Typing : {round(typing_ping, 1)} ms\n```"""
                await ctx.reply(embed=ping_emb, mention_author=False)
            else:
                ping_emb.description = f"""```ansi\n\x1b[0;1;37;40m > \x1b[0m \x1b[0;1;34mPostgreSQL\x1b[0m     \x1b[0;1;37;40m : \x1b[0m \x1b[0;1;31m{round(db_ping, 1)} ms\x1b[0m
\x1b[0;1;37;40m > \x1b[0m \x1b[0;1;34mDiscord API\x1b[0m    \x1b[0;1;37;40m : \x1b[0m \x1b[0;1;31m{websocket_ping:,.0f} ms\x1b[0m
\x1b[0;1;37;40m > \x1b[0m \x1b[0;1;34mMessage Typing\x1b[0m \x1b[0;1;37;40m : \x1b[0m \x1b[0;1;31m{round(typing_ping, 1)} ms\x1b[0m\n```"""
            await ctx.reply(embed=ping_emb, mention_author=False)

    @commands.command(
        name="banner",
        brief="View a persons banner")
    async def banner(self, ctx: GeraltContext, *, user: Union[discord.Member, discord.User] = None) -> Optional[discord.Message]:
        """See the user's Banner in an enlarged manner."""
        user = user or ctx.author
        if ctx.message.reference:
            user = ctx.message.reference.resolved.author
        fetched_user = await ctx.bot.fetch_user(user.id)
        if fetched_user.banner is None:
            return await ctx.reply(f"**{user}** does not have a banner <a:Grimacing:914905757588283422>")
        banner_emb = BaseEmbed(
            title=f"{user}'s Banner",
            colour=user.colour or user.accent_color or self.bot.colour)
        banner_emb.set_image(url=fetched_user.banner.url)
        await ctx.reply(embed=banner_emb, mention_author=False)

    # Get user's PFP
    @commands.command(
        name="avatar",
        brief="View a persons PFP",
        aliases=["pfp", "pp", "dp", "av"])
    async def avatar(self, ctx: GeraltContext, *, user: Union[discord.Member, discord.User] = None) -> Optional[discord.Message]:
        """See the user's PFP in an enlarged manner."""
        user = user or ctx.author
        if ctx.message.reference:
            user = ctx.message.reference.resolved.author
        await PFP(self.bot, ctx, user).send()

    # Get user's information
    @commands.hybrid_command(
        name="userinfo",
        brief="Get user information",
        aliases=["user", "ui"],
        with_app_command=True)
    @commands.guild_only()
    async def userinfo(self, ctx: GeraltContext, *, user: discord.Member = None) -> Optional[discord.Message]:
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
        activity = discord.utils.find(
            lambda act: isinstance(
                act,
                discord.CustomActivity),
            user.activities)
        activity_holder = f"`{discord.utils.remove_markdown(activity.name)}`" if activity and activity.name else f'`{user}` has no activity at the moment.'

        general_emb = BaseEmbed(
            title=f":scroll: {user}'s Information",
            colour=user.colour)
        general_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> General Info :",
            value=f"> <:ReplyContinued:930634770004725821> Name : {user.mention} \n"
            f"> <:ReplyContinued:930634770004725821> Nickname : {(user.nick) or 'No nickname set'} \n"
            f"> <:ReplyContinued:930634770004725821> Discriminator : `#{user.discriminator}` \n"
            f"> <:Reply:930634822865547294> Identification No. : `{user.id}` \n────")
        general_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Account Info :",
            value=f"> <:ReplyContinued:930634770004725821> Join Position : `#{sorted(ctx.guild.members, key = lambda u: u.joined_at or discord.utils.utcnow()).index(user) + 1}`\n "
            f"> <:ReplyContinued:930634770004725821> Created on : {self.bot.timestamp(user.created_at, style = 'd')} ({self.bot.timestamp(user.created_at, style = 'R')}) \n"
            f"> <:Reply:930634822865547294> Joined Guild on : {self.bot.timestamp(user.joined_at, style = 'd')} ({self.bot.timestamp(user.joined_at, style = 'R')})\n────",
            inline=False)
        general_emb.set_thumbnail(url=avatar)

        guild_emb = BaseEmbed(
            title=f":scroll: {user} in {ctx.guild}",
            colour=user.colour)
        guild_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Permissions Present :",
            value=f"> <:Reply:930634822865547294> {perms_}\n────")
        guild_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Top Most Role :",
            value=f"> <:Reply:930634822865547294> {user.top_role.mention}\n────",
            inline=False)
        guild_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> All Roles Present :",
            value=f"> <:Reply:930634822865547294> {roles}\n────",
            inline=False)
        guild_emb.set_thumbnail(url=avatar)

        misc_emb = BaseEmbed(
            title=f":scroll: {user}'s - Misc. Information",
            colour=user.colour)
        misc_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Badges Present :",
            value=f"> <:Reply:930634822865547294> {user_badges(user = user, fetch_user = fetched_user) if user_badges(user = user, fetch_user = fetched_user) else 'No Badges Present'}")
        misc_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Accent Colours :",
            value=f"> <:ReplyContinued:930634770004725821>  Banner Colour : `{str(fetched_user.accent_colour).upper()}` \n"
            f"> <:Reply:930634822865547294> Guild Role Colour : `{user.color if user.color is not discord.Color.default() else 'Default'}`\n────",
            inline=False)
        misc_emb.add_field(
            name="Activity :",
            value=f"> <:Reply:930634822865547294> {activity_holder}",
            inline=False)
        misc_emb.set_thumbnail(url=avatar)

        pfp_emb = BaseEmbed(
            title=f":scroll: {user}'s PFP",
            description=f"[**JPG Format**]({user.display_avatar.with_static_format('jpg')}) │ [**PNG Format**]({user.display_avatar.with_static_format('png')}) │ [**WEBP Format**]({user.display_avatar.with_static_format('webp')})",
            colour=user.colour)
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
                colour=user.colour)
            banner_emb.set_image(url=fetched_user.banner.url)

            embed_list = [
                general_emb,
                guild_emb,
                misc_emb,
                pfp_emb,
                banner_emb]
            async with ctx.channel.typing():
                await asyncio.sleep(0.1)
            await Paginator(self.bot, ctx, embeds=embed_list).send(ctx)

    @commands.hybrid_command(
        name="serverinfo",
        brief="Get guild information",
        aliases=["si", "gi"],
        with_app_command=True)
    @commands.guild_only()
    async def server_info(self, ctx: GeraltContext) -> Optional[discord.Message]:
        """Get entire details about the guild."""
        user_status = [
            len(list(filter(lambda u: str(u.status) == "online", ctx.guild.members))),
            len(list(filter(lambda u: str(u.status) == "idle", ctx.guild.members))),
            len(list(filter(lambda u: str(u.status) == "dnd", ctx.guild.members))),
            len(list(filter(lambda u: str(u.status) == "offline", ctx.guild.members)))
        ]
        fetched_guild = await ctx.bot.fetch_guild(ctx.guild.id)

        general_emb = BaseEmbed(
            title=f":scroll: {ctx.guild.name}'s Information",
            colour=self.bot.colour)
        general_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> General Information :",
            value=f"> │ ` ─ ` <a:Owner:905750348457738291> Owner : {ctx.guild.owner.mention} (`{ctx.guild.owner.id}`) \n"
            f"> │ ` ─ ` <a:Users:905749451350638652> No. of Roles : `{len(ctx.guild.roles)}` \n"
            f"> │ ` ─ ` <a:Info:905750331789561856> Identification No. : `{ctx.guild.id}` \n"
            f"> │ ` ─ ` <a:Verify:905748402871095336> Verification Level : {str(ctx.guild.verification_level).replace('_', ' ').replace('`NONE`', '`NILL`').title()} \n"
            f"> │ ` ─ ` <:WinFileBruh:898571301986373692> File Transfer Limit: `{humanize.naturalsize(ctx.guild.filesize_limit)}`\n────")
        general_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Initialisation :",
            value=f"> │ ` ─ ` <a:Woo:905754435379163176> Made On : {self.bot.timestamp(ctx.guild.created_at, style='d')} \n"
            f"> │ ` ─ ` <:ISus:915817563307515924> Media Filteration : For `{str(ctx.guild.explicit_content_filter).replace('_',' ').replace('`NONE`', '`NILL`').title()}` \n────",
            inline=False)
        general_emb.set_thumbnail(url=ctx.guild.icon.url)

        other_emb = BaseEmbed(
            title=f":scroll: {ctx.guild.name}'s Other Information",
            colour=self.bot.colour)
        other_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Channel Information :",
            value=f"> │ ` ─ ` <:Channel:905674680436944906> Text : `{len(ctx.guild.text_channels)}` \n"
            f"> │ ` ─ ` <:Voice:905746719034187796> Voice : `{len(ctx.guild.voice_channels)}` \n"
            f"> │ ` ─ ` <a:Thread:905750997706629130> Threads : `{len(ctx.guild.threads)}` \n"
            f"> │ ` ─ ` <:StageChannel:905674422839554108> Stage : `{len(ctx.guild.stage_channels)}` \n────",
            inline=False)
        other_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Emotes Present :",
            value=f"> │ ` ─ ` <a:IThink:933315875501641739> Animated : `{len([animated for animated in ctx.guild.emojis if animated.animated])}` / `{ctx.guild.emoji_limit}` \n"
            f"> │ ` ─ ` <:BallManHmm:933398958263386222> Non - Animated : `{len([non_animated for non_animated in ctx.guild.emojis if not non_animated.animated])}` / `{ctx.guild.emoji_limit}`\n────",
            inline=False)
        other_emb.set_thumbnail(url=ctx.guild.icon.url)

        user_emb = BaseEmbed(
            title=f":scroll: {ctx.guild.name}'s Users Information",
            colour=self.bot.colour)
        user_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> No. of User :",
            value=f"> │ ` ─ ` <a:HumanBro:905748764432662549> No. of Humans : `{len(list(filter(lambda u : u.bot is False, ctx.guild.members)))}` \n"
            f"> │ ` ─ ` <a:BotLurk:905749164355379241> No. of Bots : `{len(list(filter(lambda u : u.bot, ctx.guild.members)))}` \n"
            f"> │ ` ─ ` <a:Users:905749451350638652> Total : `{ctx.guild.member_count}`\n────",
            inline=False)
        user_emb.add_field(
            name="<:GeraltRightArrow:904740634982760459> Activity Information :",
            value=f"> │ ` ─ ` <:Online:905757053119766528> Online : `{user_status[0]}` \n"
            f"> │ ` ─ ` <:Idle:905757063064453130> Idle : `{user_status[1]}` \n"
            f"> │ ` ─ ` <:DnD:905759353141874709> Do Not Disturb : `{user_status[2]}` \n"
            f"> │ ` ─ ` <:Offline:905757032521551892> Offline : `{user_status[3]}`\n────",
            inline=False)
        user_emb.set_thumbnail(url=ctx.guild.icon.url)

        icon_emb = BaseEmbed(
            title=f":scroll: {ctx.guild.name}'s Icon",
            description=f"[**JPG Format**]({ctx.guild.icon.with_static_format('jpg')}) │ [**PNG Format**]({ctx.guild.icon.with_static_format('png')}) │ [**WEBP Format**]({ctx.guild.icon.with_static_format ('webp')})",
            colour=self.bot.colour)
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
                colour=self.bot.colour)
            banner_emb.set_image(url=fetched_guild.banner.url)

            embed_list = [
                general_emb,
                other_emb,
                user_emb,
                icon_emb,
                banner_emb]
            async with ctx.channel.typing():
                await asyncio.sleep(0.1)
            await Paginator(self.bot, ctx, embeds=embed_list).send(ctx)

    @commands.command(
        name="spotify",
        brief="Get Spotify Info.",
        aliases=["sp", "spot"])
    async def spotify(self, ctx: GeraltContext, *, user: Union[discord.Member, discord.User] = None) -> Optional[discord.Message]:
        """Get Information on what the user is listening to."""
        user = user or ctx.author
        view = discord.ui.View()
        try:
            spotify = discord.utils.find(
                lambda sp: isinstance(
                    sp, discord.Spotify), user.activities)
        except BaseException:
            return await ctx.reply(f"`{user}` is not in this guild, I'm sorry.")
        if spotify is None:
            if user == ctx.author:
                return await ctx.reply("You are not listening to Spotify right now.")
            else:
                return await ctx.reply(f"**{user}** is not listening to any song on **Spotify** right now.")
        else:
            spotify_emb = BaseEmbed(
                title=f":scroll: {user}'s Spotify Status",
                description=f"They are listening to [**{spotify.title}**]({spotify.track_url}) by - **{spotify.artist}**",
                colour=self.bot.colour)
            spotify_emb.add_field(
                name="Song Information :",
                value=f"> <:ReplyContinued:930634770004725821> ` - ` **Name :** [**{spotify.title}**]({spotify.track_url})\n"
                f"> <:ReplyContinued:930634770004725821> ` - ` **Album :** {spotify.album}\n"
                f"> <:Reply:930634822865547294> ` - ` **Duration :** \"{humanize.precisedelta(spotify.duration)}\"")
            spotify_emb.set_thumbnail(url=spotify.album_cover_url)
            view.add_item(
                discord.ui.Button(
                    label="Listen on Spotify",
                    url=spotify.track_url,
                    emoji="<a:Spotify:993120872883834990>"))
            await ctx.reply(embed=spotify_emb, mention_author=False, view=view)
