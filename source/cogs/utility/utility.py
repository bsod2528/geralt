import imghdr
import asyncio
import asyncpg
import discord
import humanize

from io import BytesIO
from discord.ext import commands
from discord import app_commands
from typing import Union, Optional, List

from ...kernel.subclasses.bot import Geralt
from ...kernel.views.paginator import Paginator
from ...kernel.subclasses.embed import BaseEmbed
from ...kernel.views.meta import PFP, Confirmation
from ...kernel.subclasses.context import GeraltContext
from ...kernel.utilities.flags import user_badges, user_perms
from ...kernel.views.history import UserHistory, SelectUserLogEvents


class Utility(commands.Cog):
    """Essesntial commands for easy life on discord."""

    def __init__(self, bot: Geralt):
        self.bot: Geralt = bot

    @property
    def emote(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(
            name="Utility",
            id=905750331789561856,
            animated=True)

    async def task_id_autocomplete(self, interaction: discord.Interaction, current: int) -> List[app_commands.Choice[int]]:
        task_deets = await self.bot.db.fetch("SELECT (task_id) FROM todo WHERE user_id = $1 ORDER BY task_id ASC", interaction.user.id)
        ids = [data[0] for data in task_deets]
        return [app_commands.Choice(name=ids, value=ids) for ids in ids]

    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User):
        if before.display_avatar != after.display_avatar:
            log_avatar = await self.bot.db.fetchval("SELECT avatar FROM user_settings WHERE user_id = $1", after.id)
            if log_avatar:
                avatar = await after.display_avatar.read()
                await self.bot.db.execute("INSERT INTO avatar_history VALUES ($1, $2, $3, $4)", after.id, avatar, discord.utils.utcnow(), imghdr.what(BytesIO(avatar)))
            return
        if before.name != after.name:
            log_username = await self.bot.db.fetchval("SELECT username FROM user_settings WHERE user_id = $1", after.id)
            if log_username:
                await self.bot.db.execute("INSERT INTO username_history VALUES ($1, $2, $3)", after.id, after.name, discord.utils.utcnow())
            return
        if before.discriminator != after.discriminator:
            log_discriminator = await self.bot.db.fetchval("SELECT discriminator FROM user_settings WHERE user_id = $1", after.id)
            if log_discriminator:
                await self.bot.db.execute("INSERT INTO discriminator_update VALUES ($1, $2, $3)", after.id, after.discriminator, discord.utils.utcnow())
            return

    @commands.command(
        name="banner",
        brief="View a persons banner")
    async def banner(self, ctx: GeraltContext, *, user: discord.Member = None) -> Optional[discord.Message]:
        """See the user's Banner in an enlarged manner."""
        user = user or ctx.author
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
    async def avatar(self, ctx: GeraltContext, *, user: discord.Member = None) -> Optional[discord.Message]:
        """See the user's PFP in an enlarged manner."""
        user = user or ctx.author
        await PFP(self.bot, ctx, user).send()

    # Get user's information
    @commands.command(
        name="userinfo",
        brief="Get user information",
        aliases=["user", "ui"])
    @commands.guild_only()
    async def userinfo(self, ctx: GeraltContext, *, user: discord.Member = None) -> Optional[discord.Message]:
        """Get entire details about a user."""
        user = user or ctx.author
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
            f"> <:ReplyContinued:930634770004725821> Created on : {self.bot.timestamp(user.created_at, style = 'D')} ({self.bot.timestamp(user.created_at, style = 'R')}) \n"
            f"> <:Reply:930634822865547294> Joined Guild on : {self.bot.timestamp(user.joined_at, style = 'D')} ({self.bot.timestamp(user.joined_at, style = 'R')})\n────",
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

    @commands.command(
        name="serverinfo",
        brief="Get guild information",
        aliases=["si", "gi"])
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
            value=f"> │ ` ─ ` <a:Woo:905754435379163176> Made On : {self.bot.timestamp(ctx.guild.created_at)} \n"
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

    @commands.hybrid_group(
        name="todo",
        brief="List User's Todo List.",
        aliases=["td"],
        with_app_command=True)
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def todo(self, ctx: GeraltContext) -> Optional[discord.Message]:
        """Sends Todo sub - commands"""
        if ctx.invoked_subcommand is None:
            await ctx.command_help()

    @todo.command(
        name="add",
        brief="Add item to your list.",
        with_app_command=True)
    @app_commands.describe(task="The task you want to complete asap.")
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def todo_add(self, ctx: GeraltContext, *, task: str) -> Optional[discord.Message]:
        """Add tasks to your todo list."""
        if len(task) > 200:
            return await ctx.reply(f"Please make sure that the `task` is below 200 characters.")
        if not task:
            return await ctx.reply(f"**{ctx.author}** ─ You have to pass in a `task` so that I can add it to your todo list.")
        else:
            await self.bot.db.execute(f"INSERT INTO todo (user_name, user_id, discriminator, task, task_created_at, url) VALUES ($1, $2, $3, $4, $5, $6) RETURNING task_id", ctx.author.name, ctx.author.id, ctx.author.discriminator, task.strip(), ctx.message.created_at, ctx.message.jump_url)
            task_id = await self.bot.db.fetchval(f"SELECT task_id FROM todo WHERE task = $1 ORDER BY task_id DESC LIMIT 1", task)
            await ctx.reply(f"Successfully added task.\n<:Reply:930634822865547294> **Task ID -** `{task_id}`")

    @todo.command(
        name="list",
        brief="See your todo list.",
        aliases=["show"],
        with_app_command=True)
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def todo_list(self, ctx: GeraltContext) -> Optional[discord.Message]:
        """See your entire todo list."""
        fetch_tasks = await self.bot.db.fetch(f"SELECT * FROM todo WHERE user_id = $1 ORDER BY task_id", ctx.author.id)
        task_list = []
        serial_no = 1
        for tasks in fetch_tasks:
            task_list.append(
                f"> [**{serial_no})**]({tasks['url']}) \"**{tasks['task']}**\"\n> │ ` ─ ` ID : {tasks['task_id']}\n> │ ` ─ ` Created : {self.bot.timestamp(tasks['task_created_at'], style = 'R')}\n────\n")
            serial_no += 1

        if not fetch_tasks:
            return await ctx.reply(f"You currently have `0` tasks present. To start listing out tasks, run `{ctx.clean_prefix}todo add <task>` <a:LifeSucks:932255208044650596>")
        else:
            if serial_no <= 3:
                todo_list_emb = BaseEmbed(
                    title=f":scroll: {ctx.author}'s Todo List :",
                    description=f"".join(tasks for tasks in task_list),
                    colour=self.bot.colour)
                todo_list_emb.set_thumbnail(url=ctx.author.display_avatar.url)
                todo_list_emb.set_footer(
                    text=f"Run {ctx.clean_prefix}todo for more sub - commands.")
                await ctx.reply(embed=todo_list_emb, mention_author=False)
            else:
                # Huge thanks to Zeus432 [ Github ID ] for helping me enable
                # the pagination :D
                embed_list = []
                while task_list:
                    todo_list_embs = BaseEmbed(
                        title=f":scroll: {ctx.author}'s Todo List :",
                        description="".join(task_list[:3]),
                        colour=self.bot.colour)
                    todo_list_embs.set_thumbnail(
                        url=ctx.author.display_avatar.url)
                    todo_list_embs.set_footer(
                        text=f"Run {ctx.clean_prefix}todo for more sub - commands.")
                    task_list = task_list[3:]
                    embed_list.append(todo_list_embs)
                await Paginator(self.bot, ctx, embeds=embed_list).send(ctx)

    @todo.command(
        name="edit",
        brief="Edit task",
        with_app_command=True)
    @app_commands.rename(task_id="id")
    @app_commands.rename(edited="content")
    @app_commands.describe(task_id="ID of your task.")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @app_commands.autocomplete(task_id=task_id_autocomplete)
    @app_commands.describe(edited="New content for the current task you want to edit.")
    async def todo_edit(self, ctx: GeraltContext, task_id: int, *, edited: str) -> Optional[discord.Message]:
        """Edit a particular task."""
        if len(edited) > 200:
            return await ctx.reply(f"Please make sure that the `edited content` is below 200 characters.")
        if task_id != await self.bot.db.fetchval(f"SELECT * FROM todo WHERE task_id = $1 AND user_name = $2", task_id, ctx.author.name):
            await ctx.reply(f"<:GeraltRightArrow:904740634982760459> **Task ID -** `{task_id}` - is a task either which you do not own or is not present in the database <:DutchySMH:930620665139191839>")
        else:
            await self.bot.db.execute(f"UPDATE todo SET task = $1, url = $2, task_created_at = $3 WHERE task_id = $4", edited.strip(), ctx.message.jump_url, ctx.message.created_at, task_id)
            await ctx.reply(f"Successfully edited **Task ID -** `{task_id}`")

    @todo.command(
        name="remove",
        brief="Removes Task",
        aliases=["finished", "done"],
        with_app_command=True)
    @app_commands.rename(task_id="id")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @app_commands.autocomplete(task_id=task_id_autocomplete)
    @app_commands.describe(task_id="ID of the task you've completed")
    async def todo_remove(self, ctx: GeraltContext, *, task_id: int) -> Optional[discord.Message]:
        """Remove a particular task."""
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{ctx.clean_prefix}{ctx.command}` for the `{ctx.command}` command <:SarahPray:920484222421045258>"

        async def yes(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.button):
            if interaction.user != ctx.author:
                return await interaction.response.send_message(content=f"{pain}", ephemeral=True)
            for view in ui.children:
                view.disabled = True
            if task_id != await self.bot.db.fetchval(f"SELECT * FROM todo WHERE task_id = $1 AND user_name = $2", task_id, ctx.author.name):
                await interaction.response.defer()
                return await ui.response.edit(content=f"<:GeraltRightArrow:904740634982760459> Task ID ─ `{task_id}` : is a task either which you do not own or is not present in the database <a:IPat:933295620834336819>", view=ui)
            else:
                await interaction.response.defer()
                await self.bot.db.execute(f"DELETE FROM todo WHERE task_id = $1", task_id)
                await ui.response.edit(content=f"Successfully removed Task ID ─ `{task_id}` <:HaroldSaysOkay:907110916104007681>", view=ui)

        async def no(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.button):
            if interaction.user != ctx.author:
                return await interaction.response.send_message(content=f"{pain}", ephemeral=True)
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            await ui.response.edit(content=f"Okay then, I haven't removed Task ID ─ `{task_id}` from your list <:DuckSip:917006564265705482>", view=ui)

        Confirmation.response = await ctx.reply(f"Are you sure you want to remove Task ID ─ `{task_id}` from your list <:BallManHmm:933398958263386222>", view=Confirmation(ctx, yes, no))

    @todo.command(
        name="clear",
        brief="Delete Todo Tasks.",
        aliases=["delete", "del", "cl"])
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def todo_clear(self, ctx: GeraltContext) -> Optional[discord.Message]:
        """Delete your entire todo list."""
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{ctx.clean_prefix}{ctx.command}` for the `{ctx.command}` command <:SarahPray:920484222421045258>"
        total = await self.bot.db.fetch(f"SELECT * FROM todo WHERE user_id = $1", ctx.author.id)
        if total == 0:
            await ctx.reply("You currently have `0` tasks present. To start listing out tasks, run `{ctx.clean_prefix}todo add <task>`")
        else:
            async def yes(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.button):
                if button.user != ctx.author:
                    return await interaction.response.send_message(content=f"{pain}", ephemeral=True)
                fetch_task = await self.bot.db.execute(f"DELETE FROM todo WHERE user_id = $1", ctx.author.id)
                for view in ui.children:
                    view.disabled = True
                if not fetch_task:
                    await interaction.response.defer()
                    await ui.response.edit(content=f"You currently have `0` tasks present. To start listing out tasks, run `{ctx.clean_prefix}todo add <TASK>` <a:CoffeeSip:907110027951742996>", view=ui)
                else:
                    await interaction.response.defer()
                    await ui.response.edit(content=f"Successfully deleted `{len(total)}` tasks from your list <:ICool:940786050681425931>.", view=ui)

            async def no(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.button):
                if button.user != ctx.author:
                    return await interaction.response.send_message(content=f"{pain}", ephemeral=True)
                for view in ui.children:
                    view.disabled = True
                await interaction.response.defer()
                await ui.response.edit(content="Okay then, I haven't deleted any `tasks` from your list <a:IEat:940413722537644033>", view=ui)

        Confirmation.response = await ctx.reply(f"Are you sure you want to delete a total of `{len(total)}` tasks in your list <a:IThink:933315875501641739>", view=Confirmation(ctx, yes, no))

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

    @commands.hybrid_command(
        name="afk",
        brief="Sets you afk.",
        with_app_command=True)
    @app_commands.describe(reason="Reason why you're going afk.")
    async def afk(self, ctx: GeraltContext, *, reason: Optional[str]):
        """Sets you afk."""
        await ctx.add_nanotick()
        await ctx.reply(f"Your afk has been set. Please enjoy!", mention_author=False)
        if not reason:
            reason = "Not Specified . . ."
        self.bot.afk[ctx.author.id] = reason
        query = "INSERT INTO afk VALUES ($1, $2, $3)"
        try:
            await self.bot.db.execute(query, ctx.author.id, reason, ctx.message.created_at)
        except asyncpg.UniqueViolationError:
            return

    @commands.group(
        name="userlog",
        brief="Logging user updates.",
        aliases=["settings", "tg", "toggle"])
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def userlog(self, ctx: GeraltContext):
        """Opt - in or out for global user update logging."""
        userlog_emb = BaseEmbed(
            title="User Logging",
            description=f"By clicking on the buttons below, you are accepting to store changes made to your `username`, `profile picture`, and `discriminator`.\n\n"
                        f"You can opt out of them at anytime and delete every information present",
            colour=self.bot.colour)
        userlog_emb.set_thumbnail(url=ctx.me.display_avatar.url)
        userlog_emb.set_footer(
            text=f"Run \"{ctx.clean_prefix}help userlog\" for more help")
        return await ctx.send(embed=userlog_emb, view=SelectUserLogEvents(self.bot, ctx))

    @userlog.command(
        name="all",
        brief="Opt - in/out for all events.")
    async def userlog_all(self, ctx: GeraltContext):
        """Opt - in/out for all events."""
        query = "INSERT INTO user_settings (user_id, discriminator, username, avatar) VALUES ($1, $2, $2, $2) " \
                "ON CONFLICT (user_id) " \
                "DO UPDATE SET avatar = $2, username = $2, discriminator = $2"
        await ctx.add_nanotick()
        await self.bot.db.execute(query, ctx.author.id, True)
        await ctx.reply(f"**{ctx.author}** ─ Successfully Opted in for all events")

    @userlog.command(
        name="avatar",
        brief="Opt - in/out for avatar logging.")
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def userlog_avatar(self, ctx: GeraltContext):
        """Opt - in/out for avatar logging."""
        query = "INSERT INTO user_settings (user_id, avatar) VALUES ($1, $2) " \
                "ON CONFLICT (user_id) " \
                "DO UPDATE SET avatar = $2"
        data = await self.bot.db.fetchval("SELECT avatar FROM user_settings WHERE user_id = $1", ctx.author.id)
        if data:
            await self.bot.db.execute(query, ctx.author.id, False)
            await ctx.reply(f"**{ctx.author}** ─ Successfully `opted out` from avatar logging <:TokoOkay:898611996163985410>")
            return await ctx.add_nanotick()

        await self.bot.db.execute(query, ctx.author.id, True)
        await ctx.reply(f"**{ctx.author}** ─ Successfully `opted in` from avatar logging <:DuckThumbsUp:917007413259956254>")
        await ctx.add_nanotick()

    @userlog.command(
        name="username",
        brief="Opt - in/out for username logging.")
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def userlog_username(self, ctx: GeraltContext):
        """Opt - in/out for username logging."""
        query = "INSERT INTO user_settings (user_id, username) VALUES ($1, $2) " \
                "ON CONFLICT (user_id) " \
                "DO UPDATE SET username = $2"
        data = await self.bot.db.fetchval("SELECT username FROM user_settings WHERE user_id = $1", ctx.author.id)
        if data:
            await self.bot.db.execute(query, ctx.author.id, False)
            await ctx.reply(f"**{ctx.author}** ─ Successfully `opted out` from username logging <:TokoOkay:898611996163985410>")
            return await ctx.add_nanotick()

        await self.bot.db.execute(query, ctx.author.id, True)
        await ctx.reply(f"**{ctx.author}** ─ Successfully `opted in` from username logging <:DuckThumbsUp:917007413259956254>")
        return await ctx.add_nanotick()

    @userlog.command(
        name="discriminator",
        brief="Opt - in/out for discriminator logging.")
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def userlog_discriminator(self, ctx: GeraltContext):
        """Opt - in/out for discriminator logging."""
        query = "INSERT INTO user_settings (user_id, discriminator) VALUES ($1, $2) " \
                "ON CONFLICT (user_id) " \
                "DO UPDATE SET discriminator = $2"
        data = await self.bot.db.fetchval("SELECT discriminator FROM user_settings WHERE user_id = $1", ctx.author.id)
        if data:
            await self.bot.db.execute(query, ctx.author.id, False)
            await ctx.reply(f"**{ctx.author}** ─ Successfully `opted out` from discriminator logging <:TokoOkay:898611996163985410>")
            return await ctx.add_nanotick()

        await self.bot.db.execute(query, ctx.author.id, True)
        await ctx.reply(f"**{ctx.author}** ─ Successfully `opted in` from discriminator logging <:DuckThumbsUp:917007413259956254>")
        return await ctx.add_nanotick()

    @userlog.command(
        name="status",
        brief="Shows your settings")
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def userlog_status(self, ctx: GeraltContext):
        fetch_deets = await self.bot.db.fetch("SELECT * FROM user_settings WHERE user_id = $1", ctx.author.id)
        data = [
            f"**Avatar Logging :** `{deets[3]}`\n**Username Logging :** `{deets[2]}`\n**Discriminator Logging :** `{deets[1]}`" for deets in fetch_deets]
        if not fetch_deets:
            return await ctx.reply(f"**{ctx.author}** ─ You haven't enabled logging at all. Please run `{ctx.clean_prefix}log` for more info.")
        log_status = BaseEmbed(
            title=f":scroll: {ctx.author}'s Log Status",
            description="".join(data),
            colour=self.bot.colour)
        log_status.set_thumbnail(url=ctx.author.display_avatar)
        await ctx.reply(embed=log_status, mention_author=False)

    @userlog.command(
        name="delete",
        brief="Delete all data",
        aliases=["reset"])
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def userlog_delete(self, ctx: GeraltContext):
        """Delete your logged data."""
        async def yes(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.Button):
            await self.bot.db.execute("DELETE FROM avatar_history WHERE user_id = $1", ctx.author.id)
            await self.bot.db.execute("DELETE FROM username_history WHERE user_id = $1", ctx.author.id)
            await self.bot.db.execute("DELETE FROM discriminator_history WHERE user_id = $1", ctx.author.id)
            await self.bot.db.execute("DELETE FROM user_settings WHERE user_id = $1", ctx.author.id)
            await ctx.add_nanotick()
            for view in ui.children:
                view.disabled = True
            await ui.response.edit(content=f"Successfully deleted your logged data", view=ui)

        async def no(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.Button):
            for view in ui.children:
                view.disabled = True
            await ui.response.edit(content=f"Seems like I'm not deleting your data.", view=ui)
            await ctx.add_nanocross()

        Confirmation.response = await ctx.reply(f"Are you sure you want to delete your data?", view=Confirmation(ctx, yes, no), allowed_mentions=self.bot.mentions)

    @commands.command(
        name="userhistory",
        brief="Get history of user.",
        aliases=["uhy"])
    @commands.cooldown(3, 15, commands.BucketType.user)
    async def user_history(self, ctx: GeraltContext, *, user: Optional[discord.User] = None):
        """Get entire history of a user."""
        user = user or ctx.author
        history_emb = BaseEmbed(
            title=f"\U0001f4dc {user}'s History",
            description=f"> [**Avatar**]({user.display_avatar.url})\n "
            f"> **Created on:** {self.bot.timestamp(user.created_at, style = 'D')} ({self.bot.timestamp(user.created_at, style = 'R')}) \n",
            colour=self.bot.colour)
        await ctx.send(embed=history_emb, view=UserHistory(self.bot, ctx, user))
