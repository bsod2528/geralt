from __future__ import annotations

import datetime
import imghdr
import io
import itertools
import traceback
from io import BytesIO
from typing import TYPE_CHECKING, Any, Optional, Union

import aiohttp
import discord
import dotenv
import psutil
import pygit2
from discord.errors import NotFound
from dotenv import dotenv_values

from ...context import BaseContext
from ...embed import BaseEmbed
from ..utilities.crucial import misc
from ..utilities.crucial import total_lines as tl

dotenv.load_dotenv()

CONFIG = dotenv_values("config.env")

if TYPE_CHECKING:
    from ...bot import BaseBot

COLOUR = discord.Colour.from_rgb(170, 179, 253)


async def modal_error(self, interaction: discord.Interaction, error: Exception) -> None:
    async with aiohttp.ClientSession() as session:
        modal_webhook = discord.Webhook.partial(
            id=CONFIG.get("ERROR_ID"), token=CONFIG.get("ERROR_TOKEN"), session=session
        )
        data = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )
        try:
            await modal_webhook.send(content=f"```py\n{data}\n```\n|| Break Point ||")
        except (discord.HTTPException, discord.Forbidden):
            await modal_webhook.send(
                file=discord.File(io.StringIO(data), filename="Traceback.py")
            )
            await modal_webhook.send(content="|| Break Point ||")
        await session.close()


# Gets latest commits from Github and Format them to make it look sexy :D


def format_commit(commit):
    short, _, _ = commit.message.partition("\n")
    commit_desc = short[0:40] + "..." if len(short) > 40 else short
    short_hash = commit.hex[0:6]
    timezone = datetime.timezone(datetime.timedelta(minutes=commit.commit_time_offset))
    commit_time = datetime.datetime.fromtimestamp(commit.commit_time).astimezone(
        timezone
    )
    timestamp = discord.utils.format_dt(commit_time, style="R")
    return f"<:GeraltRightArrow:904740634982760459> [` {short_hash} `] : [**{commit_desc}**](<https://github.com/BSOD2528/Geralt/commit/{commit.hex}>) - [ {timestamp} ]"


def latest_commit(max: int = 5):
    Repository = pygit2.Repository(".git")
    Commits = list(
        itertools.islice(
            Repository.walk(Repository.head.target, pygit2.GIT_SORT_TOPOLOGICAL), max
        )
    )
    return "\n".join(format_commit(c) for c in Commits)


# Sub - Class for " Bot Info " command.
# A huge shoutout and thanks to Zeus432 [ Github User ID ] for the amazing
# idea of adding these buttons :D


class Info(discord.ui.View):
    def __init__(self, bot: BaseBot, ctx: BaseContext):
        super().__init__(timeout=None)
        self.bot = bot
        self.ctx = ctx
        self.add_item(
            discord.ui.Button(
                label="Dashboard",
                emoji="<:AkkoComfy:907104936368685106>",
                url="https://bsod2528.me/pages/projects/geralt/geralt.html",
            )
        )
        self.add_item(
            discord.ui.Button(
                label="Support",
                emoji="<a:Comfort:918844984621428787>",
                url="https://discord.com/invite/QGxetszZPh",
            )
        )

    # Misc. Stats like No. of lines, functions and classes.
    @discord.ui.button(
        label="Misc.",
        style=discord.ButtonStyle.blurple,
        emoji="<a:WumpusVibe:905457020575031358>",
        custom_id="info-code-stats",
    )
    async def misc(self, interaction: discord.Interaction, button: discord.ui.Button):
        core_count = psutil.cpu_count()
        cpu_usage = psutil.cpu_percent()
        mem_per = psutil.virtual_memory().percent
        mem_gb = psutil.virtual_memory().available / 1024**3
        ram_usage = psutil.Process().memory_full_info().uss / 1024**2
        stats_emb = BaseEmbed(
            title="<:VerifiedDev:905668791831265290> Miscellaneous Statistics :",
            colour=COLOUR,
        )

        if interaction.user.is_on_mobile():
            stats_emb.description = (
                f"\n Shows Code Related Things :\n"
                f"```prolog\n - Total Classes    : {await misc('geralt/', '.py', 'class'):,}"
                f"\n - Total Functions  : {await misc('./', '.py', 'def'):,}"
                f"\n - Total Lines      : {await tl('./', '.py')+10}```"
            )

            stats_emb.add_field(
                name="System Usage",
                value=f"```prolog\n> CPU Usedm          : {cpu_usage:.2f} %\n"
                f"> CPU Core Count    : {core_count} Cores\n"
                f"> Memory Used       : {ram_usage:.2f} Megabytes\n"
                f"> Memory Available  : {mem_gb:.3f} GB [ {mem_per} % ]\n```",
            )
            try:
                await interaction.response.send_message(embed=stats_emb, ephemeral=True)
            except NotFound:
                return
        else:
            stats_emb.description = (
                f"\n Shows Code Related Things :\n"
                f"```ansi\n\x1b[0;1;35;40m - \x1b[0m \x1b[0;1;34mTotal Classes\x1b[0m   \x1b[0;1;35;40m : \x1b[0m \x1b[0;1;31m{await misc('./', '.py', 'class'):,}\x1b[0m"
                f"\n\x1b[0;1;35;40m - \x1b[0m \x1b[0;1;34mTotal Functions\x1b[0m \x1b[0;1;35;40m : \x1b[0m \x1b[0;1;31m{await misc('./', '.py', 'def'):,}\x1b[0m"
                f"\n\x1b[0;1;35;40m - \x1b[0m \x1b[0;1;34mTotal Lines\x1b[0m     \x1b[0;1;35;40m : \x1b[0m \x1b[0;1;31m{await tl('./', '.py'):,}\x1b[0m```"
            )
            stats_emb.add_field(
                name="System Usage",
                value=f"```ansi\n\x1b[0;1;37;40m > \x1b[0m \x1b[0;1;34mCPU Used\x1b[0m          \x1b[0;1;35;40m : \x1b[0m \x1b[0;1;31m{cpu_usage:.2f} %\x1b[0m\n"
                f"\x1b[0;1;37;40m > \x1b[0m \x1b[0;1;34mCPU Core Count\x1b[0m    \x1b[0;1;35;40m : \x1b[0m \x1b[0;1;31m{core_count} Cores\x1b[0m\n"
                f"\x1b[0;1;37;40m > \x1b[0m \x1b[0;1;34mMemory Used\x1b[0m       \x1b[0;1;35;40m : \x1b[0m \x1b[0;1;31m{ram_usage:.2f} Megabytes\x1b[0m\n"
                f"\x1b[0;1;37;40m > \x1b[0m \x1b[0;1;34mMemory Available\x1b[0m  \x1b[0;1;35;40m : \x1b[0m \x1b[0;1;31m{mem_gb:.3f} GB [ {mem_per} % ]\x1b[0m\n```",
            )
            try:
                await interaction.response.send_message(embed=stats_emb, ephemeral=True)
            except NotFound:
                return

    # Get latest Github commits
    @discord.ui.button(
        label="Github Commits",
        style=discord.ButtonStyle.blurple,
        emoji="<a:WumpusHypesquad:905661121501990923>",
        custom_id="info-repo-commits",
    )
    async def commits(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        commit_emb = BaseEmbed(
            title="<:WinGIT:898591166864441345> My Latest Changes :",
            description=f"**[Github](<https://github.com/BSOD2528/Geralt>)** repository if you want to check things out <:verykewl:916903265541689445> \n\n>>> {latest_commit(max=5)}",
            colour=COLOUR,
        )
        commit_emb.set_footer(
            text="If the link is throwing an error, it means commit has to be pushed."
        )
        try:
            await interaction.response.send_message(embed=commit_emb, ephemeral=True)
        except NotFound:
            return


# Sub - Class for Confirmation based commands which utilises buttons.


class Confirmation(discord.ui.View):
    def __init__(self, ctx: BaseContext, yes, no):
        super().__init__(timeout=None)
        self.no: Any = no
        self.ctx = ctx
        self.yes: Any = yes

    @discord.ui.button(
        label="Yes",
        style=discord.ButtonStyle.blurple,
        emoji="<:WinCheck:898572324490604605>",
    )
    async def confirmed(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.yes(self, interaction, button)

    @discord.ui.button(
        label="No",
        style=discord.ButtonStyle.danger,
        emoji="<:WinUncheck:898572376147623956>",
    )
    async def cancelled(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.no(self, interaction, button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{self.ctx.clean_prefix}{self.ctx.command}` for the `{self.ctx.command}` command <:SarahPray:920484222421045258>"
        if interaction.user != self.ctx.author:
            try:
                return await interaction.response.send_message(
                    content=f"{pain}", ephemeral=True
                )
            except NotFound:
                return
        return True


# Sub - Classes for User PFP


class PFP(discord.ui.View):
    def __init__(
        self, bot: BaseBot, ctx: BaseContext, user: Union[discord.User, discord.Member]
    ):
        super().__init__(timeout=60)
        self.bot = bot
        self.ctx = ctx
        self.user = user

        if user.id != ctx.author.id:
            self.save.disabled = True

    @discord.ui.button(
        label="JPG",
        style=discord.ButtonStyle.grey,
        emoji="<:ImageIcon:933966387477630996>",
    )
    async def jpg(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = self.user
        button.disabled = True
        await interaction.message.edit(view=self)
        try:
            await interaction.response.send_message(
                f"Download it as a [**JPG**](<{user.display_avatar.with_static_format('jpg')}>)",
                ephemeral=True,
            )
        except NotFound:
            return

    @discord.ui.button(
        label="PNG",
        style=discord.ButtonStyle.grey,
        emoji="<:ImageIcon:933966387477630996>",
    )
    async def png(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = self.user
        button.disabled = True
        await interaction.message.edit(view=self)
        try:
            await interaction.response.send_message(
                f"Download it as a [**PNG**](<{user.display_avatar.with_static_format('png')}>)",
                ephemeral=True,
            )
        except NotFound:
            return

    @discord.ui.button(
        label="WEBP",
        style=discord.ButtonStyle.grey,
        emoji="<:ImageIcon:933966387477630996>",
    )
    async def webp(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = self.user
        button.disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.send_message(
            f"Download it as a [**WEBP**](<{user.display_avatar.with_static_format('webp')}>)",
            ephemeral=True,
        )

    @discord.ui.button(
        label="Log",
        style=discord.ButtonStyle.green,
        emoji="<a:PandaNote:961260552435413052>",
    )
    async def save(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            user = self.user
            all_pfps = await self.bot.db.fetch(
                "SELECT * FROM avatar_history WHERE user_id = $1", user.id
            )
            current_pfp = await self.ctx.author.display_avatar.read()
            for pfp in all_pfps:
                if current_pfp in pfp[4]:
                    button.disabled = True
                    await interaction.message.edit(view=self)
                    return await interaction.response.send_message(
                        content=f"**{user}** - This PFP has already been logged <a:DuckPopcorn:917013065650806854>",
                        ephemeral=True,
                    )

            avatar = await user.display_avatar.read()
            async with aiohttp.ClientSession() as session:
                avatar_spam_webhook = discord.Webhook.partial(
                    id=CONFIG.get("AVATAR_SPAM_ID"),
                    token=CONFIG.get("AVATAR_SPAM_TOKEN"),
                    session=session,
                )
                sent_webhook_message = await avatar_spam_webhook.send(
                    file=discord.File(
                        BytesIO(avatar),
                        filename=f"{user}'s_avatar.{imghdr.what(BytesIO(avatar))}",
                    ),
                    wait=True,
                )
                await self.bot.db.execute(
                    "INSERT INTO avatar_history VALUES ($1, $2, $3, $4, $5)",
                    user.id,
                    str(sent_webhook_message.attachments[0]),
                    discord.utils.utcnow(),
                    imghdr.what(BytesIO(avatar)),
                    avatar,
                )
                await avatar_spam_webhook.session.close()
                button.disabled = True
                await interaction.message.edit(view=self)
                return await interaction.response.send_message(
                    content=f"**{user}** - Your PFP has been logged <a:Click:973748305416835102>",
                    ephemeral=True,
                )
        except Exception as e:
            print(e)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{self.ctx.clean_prefix}{self.ctx.command}` for the `{self.ctx.command}` command <:SarahPray:920484222421045258>"
        if interaction.user != self.ctx.author:
            try:
                return await interaction.response.send_message(
                    content=f"{pain}", ephemeral=True
                )
            except NotFound:
                return
        return True

    async def on_timeout(self) -> None:
        try:
            for view in self.children:
                view.disabled = True
                await self.message.edit(view=self)
        except NotFound:
            return

    async def send(self):
        pfp_emb = BaseEmbed(
            title=f"{str(self.user)}'s Avatar",
            url=self.user.display_avatar.url,
            colour=self.bot.colour,
        )
        pfp_emb.set_image(url=self.user.display_avatar.with_static_format("png"))

        self.message = await self.ctx.reply(
            embed=pfp_emb, view=self, mention_author=False
        )
        return self.message


# Views for leaving the guild


class Leave(discord.ui.View):
    def __init__(self, ctx: BaseContext, guild: discord.Guild):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.guild = guild

    @discord.ui.button(
        label="Leave Guild",
        style=discord.ButtonStyle.grey,
        emoji="<a:Byee:915568796536815616>",
    )
    async def leave_guild(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.guild.leave()
        button.disabled = True
        await interaction.message.edit(view=self)
        try:
            await interaction.response.send_message(
                content="Done <a:Comfort:918844984621428787>", ephemeral=True
            )
        except NotFound:
            return

    @discord.ui.button(
        label="Delete",
        style=discord.ButtonStyle.red,
        emoji="<a:Trash:906004182463569961>",
    )
    async def delete_message(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        try:
            await interaction.message.delete()
        except NotFound:
            return

    async def on_timeout(self) -> None:
        try:
            for view in self.children:
                view.disabled = True
                await self.message.edit(view=self)
        except NotFound:
            return

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        pain = f"This view can't be handled by you at the moment <:SarahPray:920484222421045258>"
        if interaction.user != self.ctx.author:
            try:
                return await interaction.response.send_message(
                    content=f"{pain}", ephemeral=True
                )
            except NotFound:
                return
        return True


# Views for the report command.


class FeedbackModal(discord.ui.Modal, title="Feedback Form"):
    def __init__(self, bot: BaseBot, ctx: BaseContext):
        super().__init__()
        self.bot = bot
        self.ctx = ctx

    feedback_title = discord.ui.TextInput(
        label="Subject",
        style=discord.TextStyle.short,
        required=True,
        placeholder="Enter the Subject.",
    )

    feedback = discord.ui.TextInput(
        label="Content",
        style=discord.TextStyle.long,
        required=True,
        placeholder="Enter your content.",
    )

    async def on_submit(self, interaction: discord.Interaction, /) -> None:
        fb_info = (
            f"- Sent By       :   {self.ctx.author} / {self.ctx.author.id}\n"
            f"- @ Guild       :   {self.ctx.guild} / {self.ctx.guild.id}\n"
            f"- @ Channel     :   {self.ctx.channel} / {self.ctx.channel.id}"
        )
        fb_emb = BaseEmbed(
            title=self.feedback_title.value.strip(),
            description=f"```yaml\n{fb_info}\n```\n[**Jump to Feedback**]({self.ctx.message.jump_url})\n",
            colour=0x2F3136,
        )
        fb_emb.add_field(
            name="Below Holds the Feedback",
            value=f"```css\n{self.feedback.value.strip()}\n```",
        )
        try:
            async with aiohttp.ClientSession() as session:
                feedback_webhook = discord.Webhook.partial(
                    id=CONFIG.get("FEEDBACK_ID"),
                    token=CONFIG.get("FEEDBACK_TOKEN"),
                    session=session,
                )
                await feedback_webhook.send(embed=fb_emb)
                await feedback_webhook.send("||  Break Point  ||")
                await session.close()
            return await interaction.response.send_message(
                content=f"**{self.ctx.author}** - Your feedback form has been sucessfully sent <a:Nod:1064213975031627897>",
                ephemeral=True,
            )
        except Exception as exception:
            support_server_link: discord.ui.View = discord.ui.View()
            support_server_link.add_item(
                discord.ui.Button(
                    label="Support Server",
                    url="discord.gg\\JXEu2AcV5Y",
                    style=discord.ButtonStyle.url,
                    emoji="<:Geralt:1064214731587604620>",
                )
            )
            return await interaction.response.send_message(
                content=f"Couldn't send your feedback form due to:```py\n{exception}\n```Please report it in the support server."
                "Click on the link below to gain access to the server!",
                ephemeral=False,
                view=support_server_link,
            )

    async def on_error(
        self, interaction: discord.Interaction, error: Exception, /
    ) -> None:
        await modal_error(self, interaction, error)


class BugModal(discord.ui.Modal, title="Bug Form"):
    def __init__(self, bot: BaseBot, ctx: BaseContext):
        super().__init__()
        self.bot = bot
        self.ctx = ctx

    bug_title = discord.ui.TextInput(
        label="Subject",
        style=discord.TextStyle.short,
        required=True,
        placeholder="Enter the Subject.",
    )

    bug_value = discord.ui.TextInput(
        label="Content",
        style=discord.TextStyle.long,
        required=True,
        placeholder="Enter your content.",
    )

    async def on_submit(self, interaction: discord.Interaction, /) -> None:
        bug_emb = (
            f"- Sent By       :   {self.ctx.author} / {self.ctx.author.id}\n"
            f"- @ Guild       :   {self.ctx.guild} / {self.ctx.guild.id}\n"
            f"- @ Channel     :   {self.ctx.channel} / {self.ctx.channel.id}"
        )
        bug_emb = BaseEmbed(
            title=self.bug_title.value.strip(),
            description=f"```yaml\n{bug_emb}\n```\n[**Jump to Feedback**]({self.ctx.message.jump_url})\n",
            colour=0x2F3136,
        )
        bug_emb.add_field(
            name="Below Holds the Bug",
            value=f"```css\n{self.bug_value.value.strip()}\n```",
        )
        try:
            async with aiohttp.ClientSession() as session:
                feedback_webhook = discord.Webhook.partial(
                    id=CONFIG.get("BUG_ID"),
                    token=CONFIG.get("BUG_TOKEN"),
                    session=session,
                )
                await feedback_webhook.send(embed=bug_emb)
                await feedback_webhook.send("||  Break Point  ||")
                await session.close()
            return await interaction.response.send_message(
                content=f"**{self.ctx.author}** - Your bug form has been sucessfully sent <a:Nod:1064213975031627897>",
                ephemeral=True,
            )
        except Exception as exception:
            support_server_link: discord.ui.View = discord.ui.View()
            support_server_link.add_item(
                discord.ui.Button(
                    label="Support Server",
                    url="discord.gg\\JXEu2AcV5Y",
                    style=discord.ButtonStyle.url,
                    emoji="<:Geralt:1064214731587604620>",
                )
            )
            return await interaction.response.send_message(
                content=f"Couldn't send your feedback form due to:```py\n{exception}\n```Please report it in the support server."
                "Click on the link below to gain access to the server!",
                ephemeral=False,
                view=support_server_link,
            )

    async def on_error(
        self, interaction: discord.Interaction, error: Exception, /
    ) -> None:
        await modal_error(self, interaction, error)


class Feedback(discord.ui.View):
    def __init__(self, bot: BaseBot, ctx: BaseContext):
        super().__init__()
        self.bot = bot
        self.ctx = ctx

    @discord.ui.button(
        label="Feedback",
        style=discord.ButtonStyle.grey,
        emoji="<:Chemistry:1057714690014314506>",
    )
    async def feedback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        try:
            await interaction.response.send_modal(FeedbackModal(self.bot, self.ctx))
        except NotFound:
            return

    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{self.ctx.clean_prefix}{self.ctx.command}` for the `{self.ctx.command}` command <:SarahPray:920484222421045258>"
        if interaction.user != self.ctx.author:
            try:
                return await interaction.response.send_message(
                    content=f"{pain}", ephemeral=True
                )
            except NotFound:
                return
        return True

    async def on_timeout(self) -> None:
        for view in self.children:
            view.disabled = True
        return await self.message.edit(view=self)


class Bug(discord.ui.View):
    def __init__(self, bot: BaseBot, ctx: BaseContext):
        super().__init__()
        self.bot = bot
        self.ctx = ctx

    @discord.ui.button(
        label="Bug",
        style=discord.ButtonStyle.grey,
        emoji="<:Maths:1057714359490588732>",
    )
    async def bug(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.send_modal(BugModal(self.bot, self.ctx))
        except NotFound:
            return

    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{self.ctx.clean_prefix}{self.ctx.command}` for the `{self.ctx.command}` command <:SarahPray:920484222421045258>"
        if interaction.user != self.ctx.author:
            try:
                return await interaction.response.send_message(
                    content=f"{pain}", ephemeral=True
                )
            except NotFound:
                return
        return True

    async def on_timeout(self) -> None:
        for view in self.children:
            view.disabled = True
        return await self.message.edit(view=self)


class Spoiler(discord.ui.View):
    def __init__(
        self,
        ctx: BaseContext,
        message: Optional[str],
    ):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.message = message

    @discord.ui.button(
        label="Reveal Spoiler",
        style=discord.ButtonStyle.grey,
        emoji="<:Warning:1105130317553074327>",
    )
    async def reveal_spoiler(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        content = f"**{self.ctx.author}** said - " + "".join(
            f"||{var}||" for var in self.message
        )
        await interaction.response.send_message(content=content, ephemeral=True)

    async def on_timeout(self) -> None:
        try:
            for view in self.children:
                view.disabled = True
                await self.msg.edit(view=self)
        except NotFound:
            return

    async def send(self):
        self.msg = await self.ctx.send(f"Spoiler message!", view=self)
        return self.msg
