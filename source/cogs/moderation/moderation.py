import discord

from discord import app_commands
from discord.ext import commands
from typing import Optional, Literal, Union

from ...kernel.subclasses.bot import Geralt
from ...kernel.views.meta import Confirmation
from ...kernel.views.paginator import Paginator
from ...kernel.subclasses.embed import BaseEmbed
from ...kernel.subclasses.context import GeraltContext


class Moderation(commands.Cog):
    """Moderation Commands for easy moderation."""

    def __init__(self, bot: Geralt):
        self.bot: Geralt = bot

    async def cog_check(self, ctx: GeraltContext) -> Literal[True]:
        if not ctx.guild:
            raise commands.NoPrivateMessage()
        return True

    @property
    def emote(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(
            name="Mod",
            id=904765450066473031,
            animated=False)

    @staticmethod
    def check_hierarchy(ctx: commands.context, user: discord.Member):
        if isinstance(user, discord.Member):
            if user == ctx.guild.owner:
                raise commands.BadArgument(f"Oh come on, they're the owner.\n")
            elif user == ctx.author:
                raise commands.BadArgument(
                    "Self Sabotage, nice... I'm not doing it -")
            elif user == ctx.guild.me:
                raise commands.BadArgument(
                    f"If you're gonna hurt me - use some other bot.")
            elif user.top_role > ctx.guild.me.top_role:
                raise commands.BadArgument(
                    f"{user} has a higher role than me. Raise my powers.")
            return

    @commands.hybrid_command(
        name="kick",
        brief="Kicks User")
    @app_commands.checks.cooldown(5, 3)
    @commands.cooldown(5, 3, commands.BucketType.user)
    @commands.has_guild_permissions(kick_members=True)
    @app_commands.describe(reason="Reason why you're kicking them.")
    @app_commands.describe(user="User you want to kick from this server.")
    async def kick(self, ctx: GeraltContext, user: discord.Member, *, reason: str = "Not Provided") -> Optional[discord.Message]:
        """Teach them a lesson by kicking them out."""
        self.check_hierarchy(ctx, user)

        async def yes(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.button):
            await user.kick(reason=f"{user} - {reason} by {ctx.author}")
            kick_emb = BaseEmbed(
                title="Kick - Has Occured.",
                description=f">>> {user.mention} has been **kicked** <a:Kicked:941667229609631765> !\n<:ReplyContinued:930634770004725821>** - ID :** `{user.id}`\n<:Reply:930634822865547294>** - On :** {self.bot.timestamp(ctx.message.created_at, style = 'F')}",
                colour=self.bot.colour)
            kick_emb.add_field(
                name="Reason :",
                value=f"```prolog\n{reason}\n```")
            kick_emb.set_thumbnail(url=user.display_avatar.url)
            for view in ui.children:
                view.disabled = True
            await interaction.response.edit_message(content=f"\u2001", embed=kick_emb, view=ui)

        async def no(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.button):
            for view in ui.children:
                view.disabled = True
            await interaction.response.edit_message(content=f"**{user.mention}** will not be kicked.", allowed_mentions=self.bot.mentions, view=ui)

        Confirmation.response = await ctx.send(f"Are you sure you want to kick {user.mention}", view=Confirmation(ctx, yes, no), allowed_mentions=self.bot.mentions)

    @commands.hybrid_command(
        name="ban",
        brief="Bans User")
    @app_commands.checks.cooldown(5, 3)
    @commands.has_guild_permissions(ban_members=True)
    @commands.cooldown(5, 3, commands.BucketType.user)
    @app_commands.describe(reason="Reason why you're banning them.")
    @app_commands.describe(user="User you want to ban from this server.")
    async def ban(self, ctx: GeraltContext, user: discord.Member, *, reason: str = "Not Provided") -> Optional[discord.Message]:
        """Teach them a lesson by banning them out."""
        self.check_hierarchy(ctx, user)

        async def yes(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.button):
            await user.ban(reason=f"{user} - {reason} by {ctx.author}")
            ban_emb = BaseEmbed(
                title="Ban - Has Occured.",
                description=f">>> {user.mention} has been **banned** <a:Banned:941667204334764042> !\n<:ReplyContinued:930634770004725821>** - ID :** `{user.id}`\n<:Reply:930634822865547294>** - On :** {self.bot.timestamp(ctx.message.created_at, style = 'F')}",
                colour=self.bot.colour)
            ban_emb.add_field(
                name="Reason :",
                value=f"```prolog\n{reason}\n```")
            ban_emb.set_thumbnail(url=user.display_avatar.url)
            for view in ui.children:
                view.disabled = True
            await interaction.response.edit_message(content=f"\u2001", embed=ban_emb, view=ui)

        async def no(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.button):
            for view in ui.children:
                view.disabled = True
            await interaction.response.edit_message(content=f"**{user.mention}** will not be banned.", allowed_mentions=self.bot.mentions, view=ui)

        Confirmation.response = await ctx.send(f"Are you sure you want to ban {user.mention}", view=Confirmation(ctx, yes, no), allowed_mentions=self.bot.mentions)

    @commands.hybrid_command(
        name="mute",
        brief="Mutes User")
    @app_commands.checks.cooldown(5, 3)
    @commands.cooldown(5, 3, commands.BucketType.user)
    @commands.has_guild_permissions(manage_roles=True)
    @app_commands.describe(user="The user you want to mute.")
    @app_commands.describe(reason="The reason why you're muting them.")
    async def mute(self, ctx: GeraltContext, user: discord.Member, *, reason: str = "Not Provided") -> Optional[discord.Message]:
        """Mute toxic users"""
        self.check_hierarchy(ctx, user)
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        if role in user.roles:
            await ctx.send(f"**{user}** already has the role and is currently muted <a:LifeSucks:932255208044650596>")
        else:
            async def yes(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.button):
                if not role:
                    create_role = await ctx.guild.create_role(name="Muted", permissions=discord.Permissions(66560), reason="Mute command needs Muted role", colour=discord.Colour.from_rgb(255, 100, 100))
                    for channel in ctx.guild.channels:
                        await channel.set_permissions(role, send_messages=False, read_messages=True, view_channel=False)

                for view in ui.children:
                    view.disabled = True

                try:
                    await user.add_roles(role, reason=reason)
                except Exception as exception:
                    await ctx.send(exception)

                mute_emb = BaseEmbed(
                    title=f"<:CustomScroll2:933390953471955004> Mute Has Occured",
                    description=f">>> {user.mention} has been **muted** <a:Mute:941667157278871612>!\n<:ReplyContinued:930634770004725821>** - ID :** `{user.id}`\n<:Reply:930634822865547294>** - On :** {self.bot.timestamp(ctx.message.created_at, style = 'F')}",
                    colour=self.bot.colour)
                mute_emb.add_field(
                    name="Reason :",
                    value=f"```prolog\n{reason}\n```")
                mute_emb.set_thumbnail(url=user.display_avatar.url)
                await user.send(embed=mute_emb)
                await interaction.response.edit_message(content=f"\u2001", embed=mute_emb, view=ui)

            async def no(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.button):
                for view in ui.children:
                    view.disabled = True
                await interaction.response.edit_message(content=f"**{user.mention}** will not be muted.", allowed_mentions=self.bot.mentions, view=ui)

        Confirmation.response = await ctx.send(f"Are you sure you want to **mute** {user.mention}\n<:Reply:930634822865547294> **- For :** {reason}", view=Confirmation(ctx, yes, no), allowed_mentions=self.bot.mentions)

    @commands.hybrid_command(
        name="unmute",
        brief="Unmutes User")
    @app_commands.checks.cooldown(5, 3)
    @commands.cooldown(5, 3, commands.BucketType.user)
    @commands.has_guild_permissions(manage_roles=True)
    @app_commands.describe(user="The user you're unmuting them.")
    @app_commands.describe(reason="The reason why you're unmuting them.")
    async def unmute(self, ctx: GeraltContext, user: discord.Member, *, reason: str = "Not Provided") -> Optional[discord.Message]:
        """Unmute users"""
        self.check_hierarchy(ctx, user)
        role = discord.utils.get(ctx.guild.roles, name="Muted")

        async def yes(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.button):
            if not role:
                create_role = await ctx.guild.create_role(name="Muted", permissions=discord.Permissions(66560), reason="Mute command needs Muted role", colour=discord.Colour.from_rgb(255, 100, 100))
                for channel in ctx.guild.channels:
                    await channel.set_permissions(role, send_messages=False, read_messages=True, view_channel=False)

            for view in ui.children:
                view.disabled = True

            try:
                await user.remove_roles(role, reason=reason)
            except Exception as exception:
                await ctx.send(exception)

            unmute_emb = BaseEmbed(
                title=f"<:CustomScroll2:933390953471955004> Unmute Has Occured",
                description=f">>> {user.mention} has been **unmuted** <a:Mute:941667157278871612>!\n<:ReplyContinued:930634770004725821>** - ID :** `{user.id}`\n<:Reply:930634822865547294>** - On :** {self.bot.timestamp(ctx.message.created_at, style = 'F')}",
                colour=self.bot.colour)
            unmute_emb.add_field(
                name=f"Reason :",
                value=f"```prolog\n{reason}\n```")
            unmute_emb.set_thumbnail(url=user.display_avatar.url)
            await user.send(embed=unmute_emb)
            await interaction.response.edit_message(content=f"\u2001", embed=unmute_emb, view=ui)

        async def no(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.button):
            for view in ui.children:
                view.disabled = True
            await interaction.response.edit_message(content=f"**{user.mention}** will not be unmuted.", allowed_mentions=self.bot.mentions, view=ui)

        Confirmation.response = await ctx.send(f"Are you sure you want to **unmute** {user.mention}\n<:Reply:930634822865547294> **- For :** {reason}", view=Confirmation(ctx, yes, no), allowed_mentions=self.bot.mentions)

    @commands.hybrid_command(
        name="setnick",
        brief="Change Nick",
        aliases=["nick"])
    @app_commands.checks.cooldown(5, 3)
    @app_commands.describe(nick="The nick name you want to set for them.")
    @app_commands.describe(user="The user you want to set / change nick name for.")
    @commands.cooldown(5, 3, commands.BucketType.user)
    @commands.has_guild_permissions(manage_nicknames=True)
    async def nick(self, ctx: GeraltContext, user: discord.Member, *, nick: str) -> Optional[discord.Message]:
        """Change the Nickname of a member"""
        self.check_hierarchy(ctx, user)

        previous_nickname = user.display_name
        await user.edit(nick=nick)
        new_nickname = nick

        nick_emb = BaseEmbed(
            title=f"<:CustomScroll1:933391442427138048> {user}'s Nick Changed!",
            description=f">>> <:GeraltRightArrow:904740634982760459> {ctx.message.author.mention} has changed {user.mention} nickname :\n\n"
            f" <:ReplyContinued:930634770004725821> **- From :** `{previous_nickname}`\n"
            f" <:Reply:930634822865547294> **- To :** `{new_nickname}`",
            colour=self.bot.colour)
        nick_emb.set_thumbnail(url=user.display_avatar.url)
        await ctx.reply(f"<:GeraltRightArrow:904740634982760459> {user.mention}'s nickname has been `changed` -\n>>> <:ReplyContinued:930634770004725821> - From : {previous_nickname}\n<:Reply:930634822865547294> - To : {new_nickname} \n**Event Occured On :** {self.bot.timestamp(discord.utils.utcnow(), style = 'F')} <a:IEat:940413722537644033>", allowed_mentions=self.bot.mentions)

    @commands.hybrid_command(
        name="purge",
        brief="Purge messages",
        aliases=["cls"])
    @app_commands.checks.cooldown(5, 3)
    @commands.cooldown(5, 3, commands.BucketType.user)
    @commands.has_guild_permissions(manage_messages=True)
    @app_commands.describe(limit="Number of messages you want to delete.")
    async def purge(self, ctx: GeraltContext, *, limit: Optional[int]) -> Optional[discord.Message]:
        """Purge Messages. Default Limit = 5"""
        if not limit:
            limit = 5
        if limit > 30:
            return await ctx.reply("Purge less than `50` SMH!")
        await ctx.channel.purge(limit=limit, bulk=False)
        return await ctx.send(f"Deleted a total of `{limit}` messages.", delete_after=2.5)

    @commands.hybrid_group(
        name="channel",
        brief="Manage Channels",
        aliases=["ch"],
        with_app_command=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def channel(self, ctx: GeraltContext) -> Optional[discord.Message]:
        if ctx.invoked_subcommand is None:
            return await ctx.command_help()

    @channel.command(
        name="lock",
        brief="Lock channels from objects.",
        aliases=["lk"],
        with_app_command=True)
    @app_commands.describe(channel="Choose the channel you want to lock.")
    @app_commands.describe(snowflake="The role or user you want to block that channel for.")
    async def lock(self, ctx: GeraltContext, channel: discord.TextChannel, snowflake: Union[discord.Member, discord.Role]) -> Optional[discord.Message]:
        """Lock user/role from using a channel."""
        async def yes(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.Button):
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            channel_overwrites = channel.overwrites_for(snowflake)
            try:
                data = self.bot.locked_objects_ids.index(snowflake.id)
            except ValueError:
                data = await self.bot.db.fetchval("SELECT object_id FROM channel_lock WHERE object_id = $1 AND guild_id = $2", snowflake.id, ctx.guild.id)
            if data:
                already_locked_emb = BaseEmbed(
                    title=f"\U0001f4dc Already Locked",
                    description=f"{snowflake.mention} has already been **locked** from {channel.mention}",
                    colour=self.bot.colour)
                return await ui.response.edit(embed=already_locked_emb, view=ui, allowed_mentions=self.bot.mentions)
            channel_overwrites.update(
                view_channel=True,
                send_messages=False,
                add_reactions=False,
                send_messages_in_threads=False)
            await channel.set_permissions(snowflake, overwrite=channel_overwrites)
            locked_emb = BaseEmbed(
                title=f"\U0001f4dc Confirmed Locking",
                description=f">>> {channel.mention} has been **locked** <a:Lock:1003635545097900112>\n<:Reply:930634822865547294> ` ─ ` for {snowflake.mention}\n────\n<:ReplyContinued:930634770004725821> ` ─ ` **Object ID -** `{snowflake.id}`\n<:Reply:930634822865547294> ` ─ ` **Channel ID -** `{channel.id}`",
                colour=self.bot.colour)
            locked_emb.set_footer(icon_url=ctx.author.display_avatar.url)
            try:
                locked_emb.set_thumbnail(url=ctx.guild.icon.url)
            except AttributeError:
                pass
            await ui.response.edit(embed=locked_emb, view=ui, allowed_mentions=self.bot.mentions)
            query = "INSERT INTO channel_lock VALUES ($1, $2, $3, $4, $5)"
            self.bot.locked_objects_ids.append(snowflake.id)
            if ctx.guild.get_role(snowflake.id):
                return await self.bot.db.execute(query, snowflake.id, channel.id, ctx.guild.id, "role", discord.utils.utcnow())
            if ctx.guild.get_member(snowflake.id):
                return await self.bot.db.execute(query, snowflake.id, channel.id, ctx.guild.id, "member", discord.utils.utcnow())

        async def no(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.Button):
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            wont_lock_emb = BaseEmbed(
                title=f"\U0001f4dc Cancelled Locking",
                description=f">>> Sure! I won't **lock** <a:AnimeSmile:915132366094209054>\n<:ReplyContinued:930634770004725821> ` ─ ` {channel.mention}\n<:Reply:930634822865547294> ` ─ ` for {snowflake.mention}\n────\n<:ReplyContinued:930634770004725821> ` ─ ` **Object ID -** `{snowflake.id}`\n<:Reply:930634822865547294> ` ─ ` **Channel ID -** `{channel.id}`",
                colour=self.bot.colour)
            wont_lock_emb.set_footer(icon_url=ctx.author.display_avatar.url)
            try:
                wont_lock_emb.set_thumbnail(url=ctx.guild.icon.url)
            except AttributeError:
                pass
            await ui.response.edit(embed=wont_lock_emb, view=ui, allowed_mentions=self.bot.mentions)

        lock_emb = BaseEmbed(
            title=f"\U0001f4dc Confirm Locking",
            description=f">>> Are you sure you want to **lock** <:SarahThonk:907109849437982750>\n<:ReplyContinued:930634770004725821> ` ─ `{channel.mention}\n<:Reply:930634822865547294> ` ─ ` for {snowflake.mention}\n────\n<:ReplyContinued:930634770004725821> ` ─ ` **Object ID -** `{snowflake.id}`\n<:Reply:930634822865547294> ` ─ ` **Channel ID -** `{channel.id}`",
            colour=self.bot.colour)
        lock_emb.set_footer(icon_url=ctx.author.display_avatar.url)
        try:
            lock_emb.set_thumbnail(url=ctx.guild.icon.url)
        except AttributeError:
            pass

        Confirmation.response = await ctx.reply(embed=lock_emb, view=Confirmation(ctx, yes, no), allowed_mentions=self.bot.mentions)

    @channel.command(
        name="unlock",
        brief="Unlock channels from objects.",
        aliases=["unlk"],
        with_app_command=True)
    @app_commands.describe(channel="Choose the channel you want to unlock.")
    @app_commands.describe(snowflake="The role or user you want to unblock that channel for.")
    async def channel_unlock(self, ctx: GeraltContext, channel: discord.TextChannel, snowflake: Union[discord.Member, discord.Role]) -> Optional[discord.Message]:
        """Unlock channels from members/roles."""
        async def yes(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.Button):
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            try:
                data = self.bot.locked_objects_ids.index(snowflake.id)
            except ValueError:
                data = await self.bot.db.fetchval("SELECT object_id FROM channel_lock WHERE object_id = $1 AND guild_id = $2", snowflake.id, ctx.guild.id)
            if not data:
                already_unlocked_emb = BaseEmbed(
                    title=f"\U0001f4dc Already Unlocked",
                    description=f"{snowflake.mention} has already been **unlocked** from {channel.mention}",
                    colour=self.bot.colour)
                already_unlocked_emb.set_footer(
                    icon_url=ctx.author.display_avatar.url)
                try:
                    already_unlocked_emb.set_thumbnail(url=ctx.guild.icon.url)
                except AttributeError:
                    pass
                return await ui.response.edit(embed=already_unlocked_emb, view=ui, allowed_mentions=self.bot.mentions)
            channel_overwrites = channel.overwrites_for(snowflake)
            channel_overwrites.update(
                view_channel=True,
                send_messages=True,
                add_reactions=True,
                send_messages_in_threads=True)
            await channel.set_permissions(snowflake, overwrite=channel_overwrites)
            unlocked_emb = BaseEmbed(
                title=f"\U0001f4dc Confirmed Unlocking",
                description=f">>> {channel.mention} has been **unlocked** <a:Lock:1003635545097900112>\n<:Reply:930634822865547294> ` ─ ` for {snowflake.mention}\n────\n<:ReplyContinued:930634770004725821> ` ─ ` **Object ID -** `{snowflake.id}`\n<:Reply:930634822865547294> ` ─ ` **Channel ID -** `{channel.id}`",
                colour=self.bot.colour)
            unlocked_emb.set_footer(icon_url=ctx.author.display_avatar.url)
            try:
                unlocked_emb.set_thumbnail(url=ctx.guild.icon.url)
            except AttributeError:
                pass
            await ui.response.edit(embed=unlocked_emb, view=ui, allowed_mentions=self.bot.mentions)
            query = "DELETE FROM channel_lock WHERE object_id = $1 AND guild_id = $2"
            await self.bot.db.execute(query, snowflake.id, ctx.guild.id)
            self.bot.locked_objects_ids.remove(snowflake.id)

        async def no(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.Button):
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            wont_unlock_emb = BaseEmbed(
                title=f"\U0001f4dc Cancelled Unlocking",
                description=f">>> Sure! I won't **unlock** <a:AnimeSmile:915132366094209054>\n<:ReplyContinued:930634770004725821> ` ─ ` {channel.mention}\n<:Reply:930634822865547294> ` ─ ` for {snowflake.mention}\n────\n<:ReplyContinued:930634770004725821> ` ─ ` **Object ID -** `{snowflake.id}`\n<:Reply:930634822865547294> ` ─ ` **Channel ID -** `{channel.id}`",
                colour=self.bot.colour)
            wont_unlock_emb.set_footer(icon_url=ctx.author.display_avatar.url)
            try:
                wont_unlock_emb.set_thumbnail(url=ctx.guild.icon.url)
            except AttributeError:
                pass
            await ui.response.edit(embed=wont_unlock_emb, view=ui, allowed_mentions=self.bot.mentions)

        unlock_emb = BaseEmbed(
            title=f"\U0001f4dc Confirm Unlocking",
            description=f">>> Are you sure you want to **unlock** <:SarahThonk:907109849437982750>\n<:ReplyContinued:930634770004725821> ` ─ `{channel.mention}\n<:Reply:930634822865547294> ` ─ ` for {snowflake.mention}\n────\n<:ReplyContinued:930634770004725821> ` ─ ` **Object ID -** `{snowflake.id}`\n<:Reply:930634822865547294> ` ─ ` **Channel ID -** `{channel.id}`",
            colour=self.bot.colour)
        unlock_emb.set_footer(icon_url=ctx.author.display_avatar.url)
        try:
            unlock_emb.set_thumbnail(url=ctx.guild.icon.url)
        except AttributeError:
            pass

        Confirmation.response = await ctx.reply(embed=unlock_emb, view=Confirmation(ctx, yes, no), allowed_mentions=self.bot.mentions)

    @channel.command(
        name="locked-list",
        brief="View locked objects",
        aliases=["list", "all"],
        with_app_command=True)
    async def channel_list(self, ctx: GeraltContext):
        """View members/roles that have been locked from certain channels"""
        fetched_locked_objects = await self.bot.db.fetch("SELECT * FROM channel_lock WHERE guild_id = $1", ctx.guild.id)
        locked_objects = []
        serial_no = 0
        for data in fetched_locked_objects:
            serial_no += 1
            if ctx.guild.get_role(data["object_id"]):
                role = ctx.guild.get_role(data["object_id"])
                locked_objects.append(
                    f"> **{serial_no}). {role.mention}**\n> │ ` ─ ` Queried At: {self.bot.timestamp(data['queried_at'], style='R')}\n> │ ` ─ ` Locked From: <#{data['channel_id']}>\n─────\n")
            if ctx.guild.get_member(data["object_id"]):
                member = ctx.guild.get_member(data["object_id"])
                locked_objects.append(
                    f"> **{serial_no}). {member.mention}**\n> │ ` ─ ` Queried At: {self.bot.timestamp(data['queried_at'], style='R')}\n> │ ` ─ ` Locked From: <#{data['channel_id']}>\n─────\n")

        if not locked_objects:
            content = f"**{ctx.author}** ─ there are no `roles` or `members` locked from any channels in **{ctx.guild}** <a:BlueGalHappy:915131837477687317>. " \
                      f"However, if you wish to lock certain channels please run `{ctx.clean_prefix}help channel` for more information <a:Comfort:918844984621428787>"
            return await ctx.reply(content)

        if serial_no <= 3:
            locked_objects_emb = BaseEmbed(
                title="\U0001f4dc Locked Objects",
                description="".join(locked_objects),
                colour=self.bot.colour)
            locked_objects_emb.set_footer(
                text=f"Run {ctx.clean_prefix}help channel for more",
                icon_url=ctx.author.display_avatar)
            try:
                locked_objects_emb.set_thumbnail(url=ctx.guild.icon.url)
            except AttributeError:
                pass
            return await ctx.reply(embed=locked_objects_emb, mention_author=False)
        embed_list = []
        while locked_objects:
            locked_objects_embs = BaseEmbed(
                title="\U0001f4dc Locked Objects",
                description="".join(locked_objects[:3]),
                colour=self.bot.colour)
            locked_objects_embs.set_footer(
                text=f"Run {ctx.clean_prefix}help channel for more",
                icon_url=ctx.author.display_avatar)
            try:
                locked_objects_embs.set_thumbnail(url=ctx.guild.icon.url)
            except AttributeError:
                pass
            locked_objects = locked_objects[3:]
            embed_list.append(locked_objects_embs)
        await Paginator(self.bot, ctx, embeds=embed_list).send(ctx)
