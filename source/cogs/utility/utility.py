import imghdr
import asyncio
import asyncpg
import aiohttp
import discord

from io import BytesIO
from discord.ext import commands
from discord import app_commands
from typing import Union, Optional, List, Dict, Tuple

from ...kernel.views.todo import SeeTask
from ...kernel.views.meta import Confirmation
from ...kernel.views.paginator import Paginator
from ...kernel.subclasses.embed import BaseEmbed
from ...kernel.subclasses.bot import Geralt, CONFIG
from ...kernel.subclasses.context import GeraltContext
from ...kernel.views.history import UserHistory, SelectUserLogEvents


class Utility(commands.Cog):
    """Essesntial commands for easy life on discord."""

    def __init__(self, bot: Geralt):
        self.bot: Geralt = bot

    @property
    def emote(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(
            name="Tools",
            id=1026029046146007050,
            animated=True)

    async def generate_highlight_emb(self, message: discord.Message, user_id: str):
        message_history: List[str] = []
        async for msg in message.channel.history(limit=5):
            stringed_msg = str(msg)
            if user_id in stringed_msg:
                return
            message_history.append(f"> [{self.bot.timestamp(msg.created_at, style='R')}] **{msg.author.name} :** {msg.content[:100]}\n")

        highlight_emb = BaseEmbed(
            title=f"You were HIghliGhTeD \U00002728",
            colour=self.bot.colour)
        highlight_emb.add_field(
            name="Recent Messages :",
            value=f"".join(message_history[::-1]))
        return highlight_emb

    async def task_id_autocomplete(self, interaction: discord.Interaction, current: int) -> List[app_commands.Choice[int]]:
        task_deets = await self.bot.db.fetch("SELECT (task_id) FROM todo WHERE user_id = $1 ORDER BY task_id ASC", interaction.user.id)
        ids = [data[0] for data in task_deets]
        return [app_commands.Choice(name=ids, value=ids) for ids in ids]

    async def trigger_list_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        try:
            cached_names = self.bot.highlight[interaction.guild.id][interaction.user.id]
            return [app_commands.Choice(name=cached_names, value=cached_names)
                for cached_names in cached_names if current.lower() in cached_names]
        except KeyError:
            trigger_list = await self.bot.db.fetch("SELECT * FROM highlight WHERE user_id = $1 AND guild_id = $2", interaction.user.id, interaction.guild.id)
            names = [f"{data[2]}" for data in trigger_list]
        return [app_commands.Choice(name=names, value=names)
                for names in names if current.lower() in names]

    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User):
        if before.display_avatar != after.display_avatar:
            log_avatar = await self.bot.db.fetchval("SELECT avatar FROM user_settings WHERE user_id = $1", after.id)
            if log_avatar:
                avatar = await after.display_avatar.read()
                async with aiohttp.ClientSession() as session:
                    avatar_spam_webhook = discord.Webhook.partial(id=CONFIG.get("AVATAR_SPAM_ID"), token=CONFIG.get("AVATAR_SPAM_TOKEN"), session=session)
                    sent_webhook_message = await avatar_spam_webhook.send(file=discord.File(BytesIO(avatar), filename=f"{after}'s_avatar.{imghdr.what(BytesIO(avatar))}"),wait=True)
                    await self.bot.db.execute("INSERT INTO avatar_history VALUES ($1, $2, $3, $4, $5)", after.id, str(sent_webhook_message.attachments[0]), discord.utils.utcnow(), imghdr.what(BytesIO(avatar)), avatar)
                    await avatar_spam_webhook.session.close()
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

    @commands.Cog.listener("on_message")
    async def highlight_people(self, message: discord.Message):
        """Core functionality for highlight."""
        if message.guild is None:
            return

        if message.author.bot:
           return

        # Could it be any better :troll:
        author_id = str(message.author.id)
        role_list = message.author.roles
        for key, value in self.bot.highlight_blocked.items():
            for user_id, object_id in value.items():
                for objects in object_id:
                    stringed_objects = str(objects)
                    if author_id in stringed_objects:
                        return
                    for roles in role_list:
                        role = str(roles.id)
                        if stringed_objects in role:
                            return

        if self.bot.highlight:
            for key, value in self.bot.highlight.items():
                for user_id, trigger_list in value.items():
                    for trigger in trigger_list:
                        if trigger in message.content.lower():
                            user = message.guild.get_member(user_id)
                            if user.id not in message.guild._members:
                                return
                            if message.author.id == user.id:
                                return
                            highlight_emb = await self.generate_highlight_emb(message, str(user.id))
                            jump_url_component = discord.ui.View()
                            jump_url_component.add_item(
                                discord.ui.Button(
                                    label="Jump to Message",
                                    emoji="<a:Jump:1024989069157077062>",
                                    url=message.jump_url))
                            return await user.send(content=f"In {message.channel.mention} for **{message.guild}** you were highlighted with the word `{trigger}`!",embed=highlight_emb, view=jump_url_component)

    @commands.hybrid_group(
        name="todo",
        brief="List User's Todo List.",
        aliases=["td"],
        with_app_command=True)
    @app_commands.checks.cooldown(2, 5)
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def todo(self, ctx: GeraltContext, *, task_id: Optional[int]) -> Optional[discord.Message]:
        """Sends Todo sub - commands"""
        if ctx.invoked_subcommand is None:
            return await ctx.command_help()


    @todo.command(
        name="add",
        brief="Add item to your list.",
        with_app_command=True)
    @app_commands.checks.cooldown(2, 5)
    @commands.cooldown(2, 5, commands.BucketType.user)
    @app_commands.describe(task="The task you want to complete asap.")
    async def todo_add(self, ctx: GeraltContext, *, task: Optional[str]) -> Optional[discord.Message]:
        """Add tasks to your todo list."""
        if ctx.message.reference:
            task = ctx.message.reference.resolved.content
        if not task:
            return await ctx.reply(f"**{ctx.author}** ─ You have to pass in a `task` so that I can add it to your todo list.")
        if len(task) > 500:
            return await ctx.reply(f"Please make sure that the `task` is below 400 characters.")
        else:
            await self.bot.db.execute(f"INSERT INTO todo (user_id, task, task_created_at, url) VALUES ($1, $2, $3, $4) RETURNING task_id", ctx.author.id, task.strip(), ctx.message.created_at, ctx.message.jump_url)
            task_id = await self.bot.db.fetchval(f"SELECT task_id FROM todo WHERE task = $1 ORDER BY task_id DESC LIMIT 1", task.strip())
            todo_add_emb = BaseEmbed(
                title=f"\U00002728 Todo Added",
                description=f"<:ReplyContinued:930634770004725821> **Task ID** : `{task_id}`\n<:Reply:930634822865547294> **Noted On **: {self.bot.timestamp(ctx.message.created_at, style='D')}",
                colour=self.bot.colour)
            todo_add_emb.add_field(
                name="Task :",
                value=f">>> {task}")
            todo_add_emb.set_thumbnail(url=ctx.author.display_avatar.url)

            await ctx.reply(embed=todo_add_emb)

    @todo.command(
        name="show",
        brief="See a task in detail.",
        aliases=["see"],
        with_app_command=True)
    @app_commands.rename(task_id="id")
    @app_commands.describe(task_id="ID of your task.")
    @commands.cooldown(2, 5, commands.BucketType.user)
    @app_commands.autocomplete(task_id=task_id_autocomplete)
    async def todo_see(self, ctx: GeraltContext, task_id: int) -> Optional[discord.Message]:
        """Check out a task in detail."""
        async with ctx.typing():
            await asyncio.sleep(1)
        if not task_id:
            return await ctx.reply(f"**{ctx.author}** ─ Give me a task id for me to fetch details.")
        fetch_task = await self.bot.db.fetch("SELECT * FROM todo WHERE task_id = $1 AND user_id = $2", task_id, ctx.author.id)
        if not fetch_task:
            return await ctx.reply(f"Couldn't find a task id of `{task_id}`. Try running another one.")
        for data in fetch_task:
            todo_show_emb = BaseEmbed(
                title=f"\U0001f4dc {ctx.author}'s Task Info",
                description=f"<:ReplyContinued:930634770004725821> **Task ID** : `{data[0]}`\n<:ReplyContinued:930634770004725821> **Jump Url** : [**Click Here**]({data[4]})\n<:Reply:930634822865547294> **Noted On** : {self.bot.timestamp(data[3], style='D')}\n────",
                colour=self.bot.colour)
            todo_show_emb.add_field(
                name="<:Join:932976724235395072> Task :",
                value=f">>> {data[2]}")
            todo_show_emb.set_thumbnail(url=ctx.author.display_avatar.url)
        todo_see_view = SeeTask(self.bot, ctx, task_id)
        todo_see_view.message = await ctx.reply(embed=todo_show_emb, view=todo_see_view)

    @todo.command(
        name="list",
        brief="See your todo list.",
        aliases=["all"],
        with_app_command=True)
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def todo_list(self, ctx: GeraltContext) -> Optional[discord.Message]:
        """See your entire todo list."""
        fetch_tasks = await self.bot.db.fetch(f"SELECT * FROM todo WHERE user_id = $1 ORDER BY task_id", ctx.author.id)
        if not fetch_tasks:
            return await ctx.reply(f"You currently have `0` tasks present. To start listing out tasks, run `{ctx.clean_prefix}todo add <task>` <a:LifeSucks:932255208044650596>")
        serial_no: int = 0
        embed_list: List = []
        for data in fetch_tasks:
            serial_no += 1
            todo_embs = BaseEmbed(
                title=f"\U0001f4dc {ctx.author}'s Todo List",
                description=f"<:ReplyContinued:930634770004725821> **Task ID** : `{data[0]}`\n<:ReplyContinued:930634770004725821> **Jump Url** : [**Click Here**]({data[4]})\n<:Reply:930634822865547294> **Noted On** : {self.bot.timestamp(data[3], style='D')}\n────",
                colour=self.bot.colour)
            todo_embs.add_field(
                name="Task :",
                value=f">>> {data[2]}")
            todo_embs.set_thumbnail(url=ctx.author.display_avatar.url)
            todo_embs.set_footer(text=f"Task Index : {serial_no} | Run {ctx.clean_prefix}todo for more help")
            embed_list.append(todo_embs)
        await Paginator(self.bot, ctx, embed_list).send(ctx)

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
        async with ctx.typing():
                await asyncio.sleep(0.5)
        if len(edited) > 500:
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
            if task_id != await self.bot.db.fetchval(f"SELECT * FROM todo WHERE task_id = $1 AND user_id = $2", task_id, ctx.author.id):
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
        query = "INSERT INTO afk VALUES ($1, $2, $3)"
        try:
            await self.bot.db.execute(query, ctx.author.id, reason, ctx.message.created_at)
            self.bot.afk[ctx.author.id] = reason
        except asyncpg.UniqueViolationError:
            return

    @commands.hybrid_group(
        name="userlog",
        brief="Logging user updates.",
        aliases=["settings", "tg", "toggle"],
        with_app_command=True)
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def userlog(self, ctx: GeraltContext):
        """Opt - in or out for global user update logging."""
        if ctx.invoked_subcommand is None:
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
        brief="Opt - in/out for all events.",
        with_app_command=True)
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
        brief="Opt - in/out for avatar logging.",
        with_app_command=True)
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
        await ctx.reply(f"**{ctx.author}** ─ Successfully `opted in` for avatar logging <:DuckThumbsUp:917007413259956254>")
        await ctx.add_nanotick()

    @userlog.command(
        name="username",
        brief="Opt - in/out for username logging.",
        with_app_command=True)
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
        await ctx.reply(f"**{ctx.author}** ─ Successfully `opted in` for username logging <:DuckThumbsUp:917007413259956254>")
        return await ctx.add_nanotick()

    @userlog.command(
        name="discriminator",
        brief="Opt - in/out for discriminator logging.",
        with_app_command=True)
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
        await ctx.reply(f"**{ctx.author}** ─ Successfully `opted in` for discriminator logging <:DuckThumbsUp:917007413259956254>")
        return await ctx.add_nanotick()

    @userlog.command(
        name="status",
        brief="Shows your settings",
        with_app_command=True)
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
        aliases=["reset"],
        with_app_command=True)
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

    @commands.hybrid_command(
        name="userhistory",
        brief="Get history of user.",
        aliases=["uhy"],
        with_app_command=True)
    @app_commands.checks.cooldown(3, 15)
    @commands.cooldown(3, 15, commands.BucketType.user)
    @app_commands.describe(user="The user you want to get information on.")
    async def user_history(self, ctx: GeraltContext, *, user: Optional[discord.User] = None):
        """Get entire history of a user."""
        user = user or ctx.author
        history_emb = BaseEmbed(
            title=f"\U0001f4dc {user}'s History",
            description=f"> [**Avatar**]({user.display_avatar.url})\n "
            f"> **Created on:** {self.bot.timestamp(user.created_at, style = 'D')} ({self.bot.timestamp(user.created_at, style = 'R')}) \n",
            colour=self.bot.colour)
        history_emb.set_image(url=user.display_avatar.url)
        await ctx.send(embed=history_emb, view=UserHistory(self.bot, ctx, user))

    @commands.hybrid_command(
        name="avatarhistory",
        brief="Get Avatar History of User.",
        aliases=["avhy"],
        with_app_command=True)
    @app_commands.describe(user="The user you want to see the avatar history of.")
    async def avatar_history(self, ctx: GeraltContext, *, user: Optional[Union[discord.User, discord.Member]] = None):
        """Get paginated view of all PFPs of a user."""
        user = user or ctx.author
        if ctx.message.reference:
            user = ctx.message.reference.resolved.author
        avatar_history = await self.bot.db.fetch("SELECT * FROM avatar_history WHERE user_id = $1", user.id)
        if not avatar_history:
            return await ctx.reply(f"**{user}** ─ has no records of previous avatars <:ForPatricksSake:915845797533335552> Please wait until they change their pfp atleast once \U0001f91d")
        if len(avatar_history) == 1:
            for x in avatar_history:
                avatar_history_emb = BaseEmbed(
                    title=f"{user}'s Avatar",
                    description=f"<:GeraltRightArrow:904740634982760459> **Changed :** {self.bot.timestamp(x[2], style='D')}",
                    colour=self.bot.colour)
                avatar_history_emb.set_image(url=x[1])
                avatar_history_emb.set_footer(text=f"Format : {x[3].capitalize()}")
                return await ctx.reply(embed=avatar_history_emb)

        embed_list = []
        for y in avatar_history:
            avatar_history_embs = BaseEmbed(
                title=f"\U0001f4dc {user}'s Avatars",
                description=f"<:GeraltRightArrow:904740634982760459> **Changed :** {self.bot.timestamp(y[2], style='D')}",
                colour=self.bot.colour)
            avatar_history_embs.set_image(url=y[1])
            avatar_history_embs.set_footer(text=f"Format : {y[3].capitalize()}")
            embed_list.append(avatar_history_embs)
        await Paginator(self.bot, ctx, embeds=embed_list).send(ctx)

    @commands.hybrid_group(
        name="highlight",
        brief="Get notified",
        aliases=["hl"],
        with_app_command=True)
    async def highlight(self, ctx: GeraltContext):
        """Get notified by triggered words!"""
        if ctx.invoked_subcommand is None:
            return await ctx.command_help()

    @highlight.command(
        name="add",
        brief="Add triggers",
        aliases=["set"],
        with_app_command=True)
    @app_commands.autocomplete(trigger=trigger_list_autocomplete)
    @app_commands.describe(
        trigger="Add a trigger word. Make sure it's not in the list above")
    async def highlight_add(self, ctx: GeraltContext, *, trigger: str = None):
        """Add trigger words to notify you."""
        if not trigger:
            return await ctx.reply(f"**{ctx.author}** - Please mention something for me to add it to your `highlight list` <:RageKill:917007995571961866>")

        if len(trigger) > 15:
            return await ctx.reply(f"**{ctx.author}** - this is not an essay writing competition! Trigger should be less than 15 characters <:SarahPout:990514983978827796>")

        try:
            query: str = "INSERT INTO highlight VALUES ($1, $2, $3, $4)"
            await self.bot.db.execute(query, ctx.author.id, ctx.guild.id, trigger.strip().lower(), discord.utils.utcnow())
            await ctx.reply(f"**{ctx.author}** - I have added `{trigger}` to your highlight list <a:AnimeSmile:915132366094209054>", delete_after=5)
            highlight_data = await self.bot.db.fetch("SELECT * FROM highlight")
            if highlight_data:
                highlight_data_list: List[Tuple] = [(data["guild_id"], data["user_id"], data["trigger"]) for data in highlight_data]
                self.bot.highlight = self.bot.generate_highlight_cache(highlight_data_list)
        except asyncpg.UniqueViolationError:
            return await ctx.reply(f"`{trigger.strip()}` - is a trigger word which is already set. Please set another word <:ICool:940786050681425931>")

    @highlight.command(
        name="remove",
        brief="Remove triggers",
        aliases=["del"],
        with_app_command=True)
    @app_commands.autocomplete(trigger=trigger_list_autocomplete)
    @app_commands.describe(
        trigger="Remove a trigger word. Make sure it's in the list above")
    async def highlight_remove(self, ctx: GeraltContext, *, trigger: str = None):
        """Remove trigger words to notify you."""
        if not trigger:
            return ctx.reply(f"**{ctx.author}** - Please mention something for me to remove it to your `highlight list`!")

        try:
            for triggers in self.bot.highlight[ctx.guild.id][ctx.author.id]:
                if trigger.strip() not in triggers:
                    return await ctx.reply(f"**{trigger}** - is a word which is not present in your `highlight trigger list`. Run `{ctx.clean_prefix}highlight list` to check triggers present <:KeanuCool:910026122383728671>")
            query = "DELETE FROM highlight WHERE user_id = $1 AND trigger = $2"
            await self.bot.db.execute(query, ctx.author.id, trigger.strip().lower())
            await ctx.reply(f"**{ctx.author}** - Removed `{trigger}` from your list <a:IEat:940413722537644033>", delete_after=5)
            highlight_data = await self.bot.db.fetch("SELECT * FROM highlight")
            highlight_data_list: List = [(data["guild_id"], data["user_id"], data["trigger"]) for data in highlight_data]
            self.bot.highlight = self.bot.generate_highlight_cache(highlight_data_list)
        except Exception as error:
            await ctx.send(error)

    @highlight.command(
        name="list",
        brief="List Your Triggers",
        aliases=["all"],
        with_app_command=True)
    async def highlight_list_triggers(self, ctx: GeraltContext):
        """See all of your trigger words."""
        trigger_data = await self.bot.db.fetch("SELECT * FROM highlight WHERE user_id = $1 AND guild_id = $2", ctx.author.id, ctx.guild.id)
        if not trigger_data:
            return await ctx.reply(f"**{ctx.author}** - You have not set any `triggers` <a:IWait:948253556190904371> Please run `{ctx.clean_prefix}highlight add` <:KeanuCool:910026122383728671>")
        trigger_list: List = [f"> <:GeraltRightArrow:904740634982760459> {data[2]}\n" for data in trigger_data]

        trigger_list_emb = BaseEmbed(
            title=f"{ctx.author}'s Trigger List",
            description="".join(trigger_list),
            colour=self.bot.colour)
        await ctx.reply(embed=trigger_list_emb, delete_after=5)

    @highlight.command(
        name="block",
        brief="Block Objects",
        aliases=["lock", "blacklist", "bl"],
        with_app_command=True)
    @app_commands.describe(object="Member or Role you want to block from highlighting you.")
    async def highlight_block(self, ctx: GeraltContext, *, object: Union[discord.Member, discord.Role]):
        """Block discord objects from highlighting you!"""
        if not object:
            return await ctx.reply(f"**{ctx.author}** - Please pass in an `object` for blocking highlights from them <:RageKill:917007995571961866>")

        if ctx.author.id == object.id:
            return await ctx.reply(f"**{ctx.author}** - You do realise that you cannot highlight yourself right <a:IPat:933295620834336819>")

        query = "INSERT INTO highlight_blocked VALUES ($1, $2, $3, $4, $5)"
        if ctx.guild.get_role(object.id):
            try:
                await ctx.add_nanotick()
                await self.bot.db.execute(query, ctx.author.id, ctx.guild.id, object.id, "channel", discord.utils.utcnow())
                await ctx.reply(f"**{object.mention}** - Has now been blocked from highlighting you in **{ctx.guild}** <:SarahPray:907109950248067154>", allowed_mentions=self.bot.mentions)
            except asyncpg.UniqueViolationError:
                await ctx.add_nanocross()
                return await ctx.reply(f"{object.mention} - Has already been blocked from highlighting you <:SIDGoesHmmMan:967421008137056276>", allowed_mentions=self.bot.mentions)

        if ctx.guild.get_member(object.id):
            try:
                await ctx.add_nanotick()
                await self.bot.db.execute(query, ctx.author.id, ctx.guild.id, object.id, "member", discord.utils.utcnow())
                await ctx.reply(f"**{object.mention}** - Has now been blocked from highlighting you in **{ctx.guild}** <:SarahPray:907109950248067154>", allowed_mentions=self.bot.mentions)
            except asyncpg.UniqueViolationError:
                await ctx.add_nanocross()
                return await ctx.reply(f"{object.mention} - Has already been blocked from highlighting you <:SIDGoesHmmMan:967421008137056276>", allowed_mentions=self.bot.mentions)

        highlight_blocked_data = await self.bot.db.fetch("SELECT * FROM highlight_blocked")
        if highlight_blocked_data:
            highlight_blocked_data_list: List = [(data["guild_id"], data["user_id"], data["object_id"]) for data in highlight_blocked_data]
            self.bot.highlight_blocked = self.bot.generate_highlight_cache(highlight_blocked_data_list)

    @highlight.command(
        name="unblock",
        brief="Unblock Objects",
        aliases=["unlock", "whitelist", "whl"],
        with_app_command=True)
    @app_commands.describe(object="Member or Role you want to unblock from highlighting you.")
    async def highlight_unblock(self, ctx: GeraltContext, *, object: Union[discord.Member, discord.Role]):
        """Unblock discord objects from highlighting you!"""
        if not object:
            return await ctx.reply(f"**{ctx.author}** - Please pass in an `object` for unblocking highlights from them <:FrogGoesHmmMan:925366780422152232>")

        query = "DELETE FROM highlight_blocked WHERE user_id = $1 AND guild_id = $2 AND object_id = $3"
        try:
            await self.bot.db.execute(query, ctx.author.id, ctx.guild.id, object.id)
            await ctx.reply(f"Successfully removed {object.mention} from your `highlight blocked` list. {object.mention} will now be able to highlight you <:RavenPray:914410353155244073>", allowed_mentions=self.bot.mentions)
            await ctx.add_nanotick()
        except Exception as error:
            return await ctx.reply(f"```py\n{error}\n```")

        highlight_blocked_data = await self.bot.db.fetch("SELECT * FROM highlight_blocked")
        if highlight_blocked_data:
            highlight_blocked_data_list: List = [(data["guild_id"], data["user_id"], data["object_id"]) for data in highlight_blocked_data]
            self.bot.highlight_blocked = self.bot.generate_highlight_cache(highlight_blocked_data_list)
        else:
            self.bot.highlight_blocked: Dict = {}

    @highlight.command(
        name="blacklisted",
        brief="Get blocked members.",
        aliases=["blocked-list", "blcklist", "blocked"],
        with_app_command=True)
    async def highlight_blocked_list(self, ctx: GeraltContext):
        """Returns List of objects you've blocked."""
        fetch_blacklisted = await self.bot.db.fetch("SELECT * FROM highlight_blocked WHERE user_id = $1 AND guild_id = $2", ctx.author.id, ctx.guild.id)
        if not fetch_blacklisted:
            return await ctx.reply(f"**{ctx.author}** - You have not blocked anyone from highlighting you in **{ctx.guild}** <:ISus:915817563307515924>")

        blacklisted: List = []
        serial_no: int = 0
        for data in fetch_blacklisted:
            serial_no += 1
            if ctx.guild.get_role(data[2]):
                blacklisted.append(f"> **{serial_no}.** Object : <@&{data[2]}>\n> Queried At : {self.bot.timestamp(data[4], style='R')}\n────\n")
            if ctx.guild.get_member(data[2]):
                blacklisted.append(f"> **{serial_no}.** Object : <@{data[2]}>\n> Queried At : {self.bot.timestamp(data[4], style='R')}\n────\n")

        if serial_no <= 3:
            blacklisted_emb = BaseEmbed(
                title=f"\U0001f4dc {ctx.author}'s Block List",
                description="".join(blacklisted),
                colour=self.bot.colour)
            blacklisted_emb.set_thumbnail(url=ctx.author.display_avatar.url)
            return await ctx.reply(embed=blacklisted_emb, mention_author=False)
        else:
            embed_list: List = []
            while blacklisted:
                blacklisted_embs = BaseEmbed(
                    title=f"\U0001f4dc {ctx.author}'s Block List",
                    description="".join(blacklisted[:3]),
                    colour=self.bot.colour)
                blacklisted = blacklisted[3:]
                blacklisted_embs.set_thumbnail(url=ctx.author.display_avatar.url)
                embed_list.append(blacklisted_embs)
            return await Paginator(self.bot, ctx, embeds=embed_list).send(ctx)
