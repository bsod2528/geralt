import asyncio
from typing import List, Optional

import asyncpg
import discord
from discord import app_commands
from discord.errors import NotFound
from discord.ext import commands

from ...bot import BaseBot
from ...context import BaseContext
from ...embed import BaseEmbed
from ...kernel.views.audit_log import MainAuditLog
from ...kernel.views.meta import Confirmation
from ...kernel.views.paginator import Paginator
from ...kernel.views.prefix import Prefix
from ...kernel.views.tickets import CallTicket, TicketSetup
from ...kernel.views.verification import SetupVerification, VerificationCall


class Guild(commands.Cog):
    """Manage the guild and my settings."""

    def __init__(self, bot: BaseBot):
        self.bot = bot

        if not self.bot.persistent_views:
            self.bot.add_view(CallTicket(self.bot, BaseContext))
            self.bot.add_view(VerificationCall(self.bot, BaseContext))

    @property
    def emote(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(
            name="Guild", id=1044584714331242496, animated=False
        )

    async def dont_archive_and_delete(self, ctx: BaseContext, ticket_id: int):
        await self.bot.db.execute(
            "DELETE FROM ticket_kernel WHERE ticket_id = $1 AND guild_id = $2",
            ticket_id,
            ctx.guild.id,
        )
        await ctx.add_nanotick()
        await asyncio.sleep(5)
        await ctx.channel.delete()
        ticket_kernel = await self.bot.db.fetch("SELECT * FROM ticket_kernel")
        ticket_kernel_list: List = [
            (data["guild_id"], data["ticket_id"], data["invoker_id"])
            for data in ticket_kernel
        ]
        self.bot.ticket_kernel = self.bot.generate_dict_cache(ticket_kernel_list)

    async def archive_and_dont_delete(self, ctx: BaseContext, ticket_id: int):
        await ctx.channel.edit(name=f"{ctx.channel.name} archived")

    async def guild_preifx_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        tag_deets = await self.bot.db.fetch(
            "SELECT UNNEST(guild_prefix) FROM prefix WHERE guild_id = $1",
            interaction.guild_id,
        )
        names = [f"{deets[0]}" for deets in tag_deets]
        return [
            app_commands.Choice(name=names, value=names)
            for names in names
            if current.lower() in names
        ]

    async def ticket_id_autocomplete(
        self, interaction: discord.Interaction, current: int
    ) -> List[app_commands.Choice[int]]:
        try:
            ids: List = []
            for key, value in self.bot.ticket_kernel.items():
                if interaction.guild.id == key:
                    for ticket_id, invoker_id in value.items():
                        ids.append(ticket_id)
        except KeyError:
            open_tickets = await self.bot.db.fetch(
                "SELECT ticket_id FROM ticket_kernel WHERE guild_id = $1 ORDER BY ticket_id ASC",
                interaction.guild.id,
            )
            ids = [data[0] for data in open_tickets]
        try:
            return [app_commands.Choice(name=ids, value=ids) for ids in ids]
        except NotFound:
            return

    async def emote_name_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        names: List[discord.Emoji.name] = []
        for emote in interaction.guild.emojis:
            if emote.animated:
                names.append(emote.name)
            names.append(emote.name)
        names.sort()
        return [app_commands.Choice(name=names, value=names) for names in names][:25]

    @commands.hybrid_group(
        name="prefix",
        brief="Prefix Related Sub-Commands",
        aliases=["p"],
        with_app_command=True,
    )
    @commands.guild_only()
    @commands.cooldown(3, 5, commands.BucketType.user)
    @commands.has_guild_permissions(manage_guild=True)
    @commands.has_guild_permissions(manage_roles=True)
    @commands.has_guild_permissions(administrator=True)
    @commands.has_guild_permissions(manage_channels=True)
    async def prefix(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Prefix related commands."""
        if ctx.invoked_subcommand is None:
            prefix_emb = BaseEmbed(
                description=f"> <:GeraltRightArrow:904740634982760459> "
                + "\n> <:GeraltRightArrow:904740634982760459> ".join(
                    await self.bot.get_prefix(ctx.message)
                ),
                colour=self.bot.colour,
            )
            prefix_emb.set_footer(text=f"Run {ctx.clean_prefix}help prefix.")
            if ctx.guild.icon.url:
                prefix_emb.set_author(
                    name=f"{len(await self.bot.get_prefix(ctx.message))} Prefixes ─ {ctx.guild}",
                    icon_url=ctx.guild.icon.url,
                )
            else:
                prefix_emb.set_author(name=ctx.guild)
            prefix_view = Prefix(self.bot, ctx)
            prefix_view.message = await ctx.reply(
                embed=prefix_emb, view=prefix_view, mention_author=False
            )

    @prefix.command(
        name="add", brief="Add Custom Prefixes", aliases=["a"], with_app_command=True
    )
    @app_commands.checks.cooldown(3, 5)
    @commands.cooldown(3, 5, commands.BucketType.user)
    @app_commands.autocomplete(prefix=guild_preifx_autocomplete)
    @app_commands.describe(
        prefix="Make sure you're not entering the same prefix as shown here!"
    )
    async def prefix_add(
        self, ctx: BaseContext, *, prefix: Optional[str]
    ) -> Optional[discord.Message]:
        """Add a custom prefix."""
        total_prefixes = await self.bot.get_prefix(ctx.message)
        if not prefix:
            return await ctx.reply("Pass in a `prefix` for me to add from the list.")
        if prefix.strip() == ".g":
            return await ctx.reply(
                f"**{ctx.author}** - `.g` is the default prefix, so you can't add that lmao <:SarahLaugh:907109900952420373>"
            )
        if len(total_prefixes) > 14:
            return await ctx.reply(
                f"For **{ctx.guild}** - The maximum of `15` prefixes has reached. To add more, please remove other custom prefixes <:SarahYay:990543210235461682>"
            )
        if prefix is None:
            return await ctx.reply(
                "You do realise you have to enter a `new prefix` for that to become the prefix for this guild? <:SarahPout:989816223544012801>"
            )
        if len(prefix) > 15:
            return await ctx.reply(
                "You're definitely going to ace that essay writing competition <:SarahLaugh:907109900952420373>"
            )
        if prefix == "--":
            return await ctx.reply(
                f"I'm afraid that `--` cannot be set as a guild prefix. As it is used for invoking flags. Try another one."
            )
        try:
            fetched_data = await self.bot.db.fetch(
                "SELECT UNNEST(guild_prefix) FROM prefix WHERE guild_id = $1",
                ctx.guild.id,
            )
            for present_prefixes in fetched_data:
                if prefix in str(present_prefixes):
                    return await ctx.send(f"{prefix} is already present")
            query = (
                "INSERT INTO prefix VALUES ($1, ARRAY [$2, '.g']) ON CONFLICT (guild_id) "
                "DO UPDATE SET guild_prefix = ARRAY_APPEND(prefix.guild_prefix, $2) WHERE prefix.guild_id = $1"
            )
            await self.bot.db.execute(query, ctx.guild.id, prefix)
            data = await self.bot.db.fetch("SELECT guild_id, guild_prefix FROM prefix")
            for guild_id, prefixes in data:
                self.bot.prefixes[guild_id] = set(prefixes)
            await ctx.reply(
                f"**{ctx.message.author}** - `{prefix}` has been added to my prefix list for **{ctx.guild.name}** <:SarahLaugh:907109900952420373>"
            )
        except Exception as exception:
            await ctx.add_nanocross()
            return await ctx.send(f"```py\n{exception}\n```")

    @prefix.command(
        name="remove", brief="Remove a prefix.", aliases=["del"], with_app_command=True
    )
    @app_commands.checks.cooldown(3, 5)
    @commands.cooldown(3, 5, commands.BucketType.user)
    @app_commands.autocomplete(prefix=guild_preifx_autocomplete)
    @app_commands.describe(prefix="Give in the prefix you want to you remove.")
    async def prefix_remove(
        self, ctx: BaseContext, *, prefix: Optional[str]
    ) -> Optional[discord.Message]:
        """Remove a custom prefix."""
        if not prefix:
            return await ctx.reply("Pass in a `prefix` for me to remove from the list.")
        if prefix.strip() == ".g":
            return await ctx.reply(
                f"**{ctx.author}** - `.g` is the default prefix, so you can't remove that lmao <:SarahLaugh:907109900952420373>"
            )
        try:
            fetched_prefixes = "\n".join(
                await self.bot.get_prefix(ctx.message or discord.Interaction.channel)
            )
            if prefix.strip() not in fetched_prefixes:
                return await ctx.reply(
                    f"`{prefix}` - is not in the guild's prefix list for **{ctx.guild}** <:SarahPout:989816223544012801>"
                )
            query = "UPDATE prefix SET guild_prefix = ARRAY_REMOVE(prefix.guild_prefix, $2) WHERE guild_id = $1"
            await self.bot.db.execute(query, ctx.guild.id, prefix)
            data = await self.bot.db.fetch("SELECT guild_id, guild_prefix FROM prefix")
            for guild_id, prefixes in data:
                self.bot.prefixes[guild_id] = set(prefixes)
            await ctx.add_nanotick()
            await ctx.reply(
                f"**{ctx.message.author}** - `{prefix}` has been removed to my prefix list for **{ctx.guild.name}** <:SarahLaugh:907109900952420373>"
            )
        except Exception as exception:
            await ctx.add_nanocross()
            return await ctx.send(f"```py\n{exception}\n```")

    @prefix.command(
        name="reset", brief="Reset all custom prefixes", with_app_command=True
    )
    @app_commands.checks.cooldown(3, 5)
    async def prefix_reset(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Reset all the prefixes back to `.g`"""
        data = await self.bot.db.fetch(
            "SELECT UNNEST(guild_prefix) FROM prefix WHERE guild_id = $1", ctx.guild.id
        )
        self.bot.prefixes[ctx.guild.id] = {
            ".g",
        }
        await ctx.send(f"Reset all the `{len(data)}` prefixes back to `.g`.")
        await ctx.add_nanotick()
        return await self.bot.db.execute(
            "DELETE FROM prefix WHERE guild_id = $1", ctx.guild.id
        )

    # Todo - Rewrite this whole thing because it's messy.
    @commands.hybrid_group(
        name="ticket",
        brief="Ticket - Tool for you server.",
        aliases=["tt", "tools"],
        with_app_command=True,
    )
    @commands.guild_only()
    @commands.cooldown(3, 20, commands.BucketType.user)
    @commands.has_guild_permissions(administrator=True)
    @commands.has_guild_permissions(manage_channels=True)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def ticket(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Ticketing system for support in your guild."""
        if ctx.invoked_subcommand is None:
            await ctx.command_help()

    @ticket.command(name="setup", brief="Set-up ticket system.", with_app_command=True)
    @commands.has_guild_permissions(administrator=True)
    @app_commands.describe(channel="Channel you want members to raise a ticket from.")
    async def ticket_setup(
        self, ctx: BaseContext, *, channel: discord.TextChannel = None
    ) -> Optional[discord.Message]:
        """Setup ticket system in your server.
        ────
        **Example :**
        `.gticket setup #channel / channel / 123456789012345678`
        ────"""
        if ctx.guild.id in self.bot.ticket_init:
            return await ctx.reply(
                f"**{ctx.author}** - Ticket System is already present in `{ctx.guild}`. Run `{ctx.clean_prefix}ticket status` to see more <a:FrogHappy:915131835808383016>"
            )
        if not channel:
            return await ctx.reply(
                f"To set up ticket system, you have to `mention` / `send the id` / `type the name of the channel` for me to send the main panel over there <a:LifeSucks:932255208044650596>"
            )
        await TicketSetup(self.bot, ctx, channel).send()

    @ticket.command(
        name="pending", brief="Check pending tickets", with_app_command=True
    )
    async def ticket_pending(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Review pending tickets."""
        try:
            enabled_bool = self.bot.ticket_init[ctx.guild.id]
        except KeyError:
            enabled_bool = await self.bot.db.fetch(
                "SELECT * FROM ticket_init WHERE guild_id = $1", ctx.guild.id
            )
        if not enabled_bool:
            return await ctx.reply(
                f"**{ctx.guild}** has not set up Ticket System. To setup, run `{ctx.clean_prefix}ticket` <a:IWait:948253556190904371>"
            )

        fetched_data = await self.bot.db.fetch(
            "SELECT * FROM ticket_kernel WHERE guild_id = $1", ctx.guild.id
        )
        if not fetched_data:
            return await ctx.reply(
                f"**{ctx.author}** - There are no tickets opened in **{ctx.guild}** at the moment <a:Click:973748305416835102>"
            )

        pending_tickets_list: List[str] = [
            f"> <:ReplyContinued:930634770004725821> **Ticket ID:** `{data[0]}`\n> <:ReplyContinued:930634770004725821> **Opened By:** {ctx.guild.get_member(data[2]).mention}\n> <:Reply:930634822865547294> **At Channel:** {ctx.guild.get_channel(data[3]).mention}\n───\n"
            for data in fetched_data
        ]

        if len(pending_tickets_list) > 3:
            embed_list: List[BaseEmbed] = []
            while pending_tickets_list:
                pending_tickets_embs = BaseEmbed(
                    title=f"\U0001f4dc Tickets Pending in {ctx.guild}",
                    description="".join(pending_tickets_list[:3]),
                    colour=self.bot.colour,
                )
                pending_tickets_list = pending_tickets_list[3:]
                embed_list.append(pending_tickets_embs)
            return await Paginator(self.bot, ctx, embeds=embed_list).send(ctx)

        pending_tickets_emb = BaseEmbed(
            title=f"\U0001f4dc Tickets Pending in {ctx.guild}",
            description="".join(pending_tickets_list),
            colour=self.bot.colour,
        )
        await ctx.send(embed=pending_tickets_emb)

    @ticket.command(name="close", brief="Close a ticket.", with_app_command=True)
    @app_commands.rename(ticket_id="ticket-id")
    @app_commands.autocomplete(ticket_id=ticket_id_autocomplete)
    @app_commands.describe(ticket_id="The ID of the ticket you want to close.")
    async def ticket_close(
        self, ctx: BaseContext, ticket_id: Optional[int]
    ) -> Optional[discord.Message]:
        """Close a ticket."""
        try:
            enabled_bool = self.bot.ticket_init[ctx.guild.id]
        except KeyError:
            enabled_bool = await self.bot.db.fetch(
                "SELECT * FROM ticket_init WHERE guild_id = $1", ctx.guild.id
            )
        if not enabled_bool:
            return await ctx.reply(
                f"**{ctx.guild}** has not set up Ticket System. To setup, run `{ctx.clean_prefix}ticket` <a:IWait:948253556190904371>"
            )

        if not ticket_id:
            return await ctx.reply(
                f"**{ctx.author}** - Please pass in the `ticket_id` to close it."
            )

        fetched_data = await self.bot.db.fetch(
            "SELECT * FROM ticket_kernel WHERE guild_id = $1", ctx.guild.id
        )
        if not fetched_data:
            return await ctx.reply(
                f"**{ctx.author}** - There are no tickets opened in **{ctx.guild}** at the moment <a:Click:973748305416835102>"
            )

        for key, value in self.bot.ticket_kernel.items():
            if ctx.guild.id == key:
                if ticket_id not in value:
                    first_message: discord.Message = [
                        messag
                        async for messag in ctx.channel.history(
                            oldest_first=True, limit=1
                        )
                    ][0]
                    view = discord.ui.View()
                    view.add_item(
                        discord.ui.Button(
                            label="Jump to First Message",
                            style=discord.ButtonStyle.url,
                            emoji="<a:LifeSucks:932255208044650596>",
                            url=first_message.jump_url,
                        )
                    )
                    return await ctx.reply(
                        f"**{ctx.author}** - There is no such ticket with the ID of `{ticket_id}` <:DutchySMH:930620665139191839> Click on the button to check the `ticket-id`.",
                        view=view,
                    )

        async def yes(
            ui: discord.ui.View,
            interaction: discord.Interaction,
            button: discord.ui.Button,
        ):
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            await ui.response.edit(
                content="Archiving this ticket.",
                view=ui,
                allowed_mentions=self.bot.mentions,
            )
            await self.archive_and_dont_delete(ctx, ticket_id)
            await ui.response.edit(
                content="Archived", view=ui, allowed_mentions=self.bot.mentions
            )

        async def no(
            ui: discord.ui.View,
            interaction: discord.Interaction,
            button: discord.ui.Button,
        ):
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            await ui.response.edit(
                content=f"{ctx.channel.mention} will be deleted in 5 seconds",
                view=ui,
                allowed_mentions=self.bot.mentions,
            )
            await self.dont_archive_and_delete(ctx, ticket_id)

        details = await self.bot.db.fetch(
            "SELECT * FROM ticket_kernel WHERE guild_id = $1 AND ticket_id = $2",
            ctx.guild.id,
            ticket_id,
        )
        for deet in details:
            if ctx.channel.id != deet[3]:
                return await ctx.reply(
                    f"**{ctx.author}** - Please go to {ctx.guild.get_channel(deet[3]).mention} and run `{ctx.clean_prefix}ticket close {ticket_id}`."
                )

        fetch_id = await self.bot.db.fetch(
            "SELECT * FROM ticket_kernel WHERE guild_id = $1 AND ticket_id = $2 AND channel_id = $3",
            ctx.guild.id,
            ticket_id,
            ctx.channel.id,
        )
        for data in fetch_id:
            if data[3] == ctx.channel.id:
                Confirmation.response = await ctx.reply(
                    "Do you want to archive this ticket?",
                    view=Confirmation(ctx, yes, no),
                    mention_author=False,
                )

    @ticket.command(name="status", brief="Status of ticket system.")
    async def ticket_status(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Returns the ticket system status for this guild."""
        view = discord.ui.View()
        try:
            system_status = [
                f"> <:Join:932976724235395072> Category ID : `{self.bot.ticket_init[ctx.guild.id][0]}`\n> <:Join:932976724235395072> Panel Message ID : `{self.bot.ticket_init[ctx.guild.id][2]}`"
            ]
            if not system_status:
                return await ctx.reply(
                    f"**{ctx.guild}** has not set up Ticket System. To setup, run `{ctx.clean_prefix}ticket` <a:IWait:948253556190904371>"
                )
            view.add_item(
                discord.ui.Button(
                    label="Jump to Panel",
                    style=discord.ButtonStyle.url,
                    emoji="<a:Click:973748305416835102>",
                    url=self.bot.ticket_init[ctx.guild.id][3],
                )
            )
        except KeyError:
            fetch_deets = await self.bot.db.fetch(
                "SELECT * FROM ticket_init WHERE guild_id = $1", ctx.guild.id
            )
            system_status = [
                f"> <:Join:932976724235395072> Category ID : `{data['category_id']}`\n> <:Join:932976724235395072> Panel Message ID : `{data['sent_message_id']}`"
                for data in fetch_deets
            ]
            if not fetch_deets:
                return await ctx.reply(
                    f"**{ctx.guild}** has not set up Ticket System. To setup, run `{ctx.clean_prefix}ticket` <a:IWait:948253556190904371>"
                )
            view.add_item(
                discord.ui.Button(
                    label="Jump to Panel",
                    style=discord.ButtonStyle.url,
                    emoji="<a:Click:973748305416835102>",
                    url=data["jump_url"],
                )
                for data in fetch_deets
            )

        status_emb = BaseEmbed(
            title=f"{ctx.guild}'s Ticket System Status",
            description="".join(system_status),
            colour=self.bot.colour,
        )
        status_emb.set_thumbnail(url=ctx.guild.icon.url)
        await ctx.reply(embed=status_emb, view=view, mention_author=False)

    @ticket.command(
        name="dismantle",
        brief="Dismantles Ticket System.",
        aliases=["delete", "remove", "clear"],
    )
    async def ticket_dismantle(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Disables the ticket system in your guild."""
        try:
            enabled_bool = self.bot.ticket_init[ctx.guild.id]
        except KeyError:
            enabled_bool = await self.bot.db.fetch(
                "SELECT * FROM ticket_init WHERE guild_id = $1", ctx.guild.id
            )
        if not enabled_bool:
            return await ctx.reply(
                f"**{ctx.guild}** has not set up Ticket System. To setup, run `{ctx.clean_prefix}ticket` <a:IWait:948253556190904371>"
            )

        if ctx.guild.id not in self.bot.ticket_init:
            return await ctx.reply(
                f"**{ctx.author}** - Ticket System has already been disabled in **{ctx.guild}** <a:DuckPopcorn:917013065650806854>"
            )

        async def yes(
            ui: discord.ui.View,
            interaction: discord.Interaction,
            button: discord.ui.Button,
        ):
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            try:
                try:
                    cache = self.bot.ticket_init[ctx.guild.id]
                    await self.bot.http.delete_message(cache[1], cache[2])
                except KeyError:
                    channel = await self.bot.db.fetchval(
                        "SELECT sent_channel_id FROM ticket_init WHERE guild_id = $1",
                        ctx.guild.id,
                    )
                    message = await self.bot.db.fetchval(
                        "SELECT sent_message_id FROM ticket_init WHERE guild_id = $1",
                        ctx.guild.id,
                    )
                    await self.bot.http.delete_message(channel, message)
                try:
                    query_one = "DELETE FROM ticket_init WHERE guild_id = $1 "
                    query_two = "DELETE FROM ticket_kernel WHERE guild_id = $1"
                    await self.bot.db.execute(query_one, ctx.guild.id)
                    await self.bot.db.execute(query_two, ctx.guild.id)
                    del self.bot.ticket_init[ctx.guild.id]
                    del self.bot.ticket_kernel[ctx.guild.id]
                except asyncpg.errors as error:
                    return await ui.response.edit(
                        content=f"```py\n{error}\n```",
                        view=ui,
                        allowed_mentions=self.bot.mentions,
                    )
                await ui.response.edit(
                    content=f"Successfully dismantled the `ticket system` from **{ctx.guild}** <a:DecayerVibe:910196112458145833>",
                    view=ui,
                    allowed_mentions=self.bot.mentions,
                )
                await ctx.add_nanotick()
            except discord.errors.NotFound:
                return await ui.response.edit(
                    content="It seems you have already executed this command <a:IThink:933315875501641739>",
                    view=ui,
                    allowed_mentions=self.bot.mentions,
                )
            await ctx.add_nanotick()

        async def no(
            ui: discord.ui.View,
            interaction: discord.Interaction,
            button: discord.ui.Button,
        ):
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            await ui.response.edit(
                content="Seems like I'm not dismantling the ticket-system <a:AnimeSmile:915132366094209054>",
                view=ui,
                allowed_mentions=self.bot.mentions,
            )

        Confirmation.response = await ctx.reply(
            "Are you sure you want to dismantle the ticket-system?",
            view=Confirmation(ctx, yes, no),
            mention_author=False,
        )

    @commands.hybrid_group(
        name="verification",
        brief="Verification commands",
        aliases=["verify", "vf"],
        with_app_command=True,
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    @commands.cooldown(3, 20, commands.BucketType.user)
    @commands.has_guild_permissions(administrator=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.max_concurrency(1, commands.BucketType.guild)
    async def verification(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Group commands for securing your guild."""
        if ctx.invoked_subcommand is None:
            return await ctx.command_help()

    @verification.command(name="setup", brief="Setup", with_app_command=True)
    @app_commands.describe(channel="The channel you want users to get verified at.")
    async def verification_setup(
        self, ctx: BaseContext, channel: Optional[discord.TextChannel]
    ) -> Optional[discord.Message]:
        """Secure your guild with verification."""
        if ctx.guild.id in self.bot.verification:
            return await ctx.reply(
                f"**{ctx.author}** - verification system has already been setup in **{ctx.guild} <a:ImSorryWhat:923941819266527304> Run `{ctx.clean_prefix}verification status`"
            )
        if not channel:
            return await ctx.reply(
                f"**{ctx.author}** - please `mention`, or send `channel id`, or `type the channel name` to setup the verification system."
            )
        await SetupVerification(self.bot, ctx, channel).send()

    @verification.command(
        name="dismantle", brief="Dismantle verification system", aliases=["remove"]
    )
    async def verification_dismantle(
        self, ctx: BaseContext
    ) -> Optional[discord.Message]:
        """Dismantle verification system from your server."""

        async def yes(
            ui: discord.ui.View,
            interaction: discord.Interaction,
            button: discord.ui.Button,
        ):
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            try:
                query = "DELETE FROM verification WHERE guild_id = $1"
                try:
                    cache = self.bot.verification[ctx.guild.id]
                    await self.bot.http.delete_message(cache[3], cache[4])
                except KeyError:
                    channel = await self.bot.db.fetchval(
                        "SELECT channel_id FROM verification WHERE guild_id = $1",
                        ctx.guild.id,
                    )
                    message = await self.bot.db.fetchval(
                        "SELECT message_id FROM verification WHERE guild_id = $1",
                        ctx.guild.id,
                    )
                    await self.bot.http.delete_message(channel, message)
                await self.bot.db.execute(query, ctx.guild.id)
                del self.bot.verification[ctx.guild.id]
            except Exception:
                await ctx.add_nanocross()
                return await ui.response.edit(
                    content=f"Verification system hasn't been set-up for **{ctx.guild}** <:SarahPout:990514983978827796> Run `{ctx.clean_prefix}verification setup",
                    view=ui,
                    allowed_mentions=self.bot.mentions,
                )
            await ctx.add_nanotick()
            return await ui.response.edit(
                content=f"Successfully removed the verification system for **{ctx.guild}** <:KeanuCool:910026122383728671>",
                view=ui,
                allowed_mentions=self.bot.mentions,
            )

        async def no(
            ui: discord.ui.View,
            interaction: discord.Interaction,
            button: discord.ui.Button,
        ):
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            await ui.response.edit(
                content=f"Alright, I am not dismantling the verification system here <:RavenPray:914410353155244073>",
                view=ui,
                allowed_mentions=self.bot.mentions,
            )

        Confirmation.response = await ctx.reply(
            "Are you sure you want to dismantle the verification system <:SIDGoesHmmMan:967421008137056276>",
            view=Confirmation(ctx, yes, no),
            mention_author=False,
        )

    @verification.command(
        name="status", brief="Verification Status", with_app_command=True
    )
    async def verification_status(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Returns verification status for your guild."""
        try:
            cache = self.bot.verification[ctx.guild.id]
            status = [
                f"> <:One:989876071052750868>**Question:**\n> {cache[0]}\n────\n> <:Two:989876145291948122> **Answer:**\n> {cache[1]}\n────\n> <:Three:989876184420610099>**Present In:**\n> <#{cache[3]}>"
            ]
        except KeyError:
            data = await self.bot.db.fetch(
                "SELECT * FROM verification WHERE guild_id = $1", ctx.guild.id
            )
            status = [
                f"> <:One:989876071052750868>**Question:**\n> {deets[1]}\n────\n> <:Two:989876145291948122> **Answer:**\n> {deets[2]}\n────\n> <:Three:989876184420610099>**Present In:**\n> <#{deets[4]}>"
                for deets in data
            ]
        if not status:
            return await ctx.reply(
                f"**{ctx.author}** - verification system hasn't been setup for `{ctx.guild}`. Please run `{ctx.clean_prefix}help verification` for more information."
            )
        verification_status_emb = BaseEmbed(
            title=f"Verification Status for {ctx.guild}",
            description="".join(status),
            colour=self.bot.colour,
        )
        verification_status_emb.set_footer(
            text=f"Run {ctx.clean_prefix}help verification.",
            icon_url=ctx.author.display_avatar,
        )
        try:
            verification_status_emb.set_thumbnail(url=ctx.guild.icon.url)
        except AttributeError:
            pass
        await ctx.send(embed=verification_status_emb)

    @commands.hybrid_group(
        name="guild", brief="Guild Settings", aliases=["server"], with_app_command=True
    )
    @commands.guild_only()
    @commands.cooldown(3, 20, commands.BucketType.user)
    @commands.has_guild_permissions(administrator=True)
    @commands.has_guild_permissions(manage_channels=True)
    async def guild(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Sub-commands for basic guild settings"""
        if ctx.invoked_subcommand is None:
            return await ctx.command_help()

    @guild.command(
        name="snipe",
        brief="Opt - in/out for sniping.",
        aliases=["s"],
        with_app_command=True,
    )
    async def guild_snipe(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Opt - in/out for sniping messages!"""
        query: str = (
            "INSERT INTO guild_settings VALUES ($1, $2) "
            "ON CONFLICT (guild_id) "
            "DO UPDATE SET snipe = $2 WHERE guild_settings.guild_id = $1"
        )
        data = await self.bot.db.fetchval(
            "SELECT snipe FROM guild_settings WHERE guild_id = $1", ctx.guild.id
        )
        if data == True:
            await ctx.reply(
                f"I will hereby `not snipe` all edited & deleted messages in **{ctx.guild.name}** \U0001f91d"
            )
            await ctx.add_nanotick()
            self.bot.settings[ctx.guild.id]["snipe"] = False
            return await self.bot.db.execute(query, ctx.guild.id, False)

        await ctx.reply(
            f"I will hereby `snipe` all edited & deleted messages in **{ctx.guild.name}** \U0001f91d"
        )
        await ctx.add_nanotick()
        self.bot.settings[ctx.guild.id]["snipe"] = True
        return await self.bot.db.execute(query, ctx.guild.id, True)

    @guild.command(
        name="auditlog",
        brief="View the Audit Log",
        aliases=["al"],
        with_app_command=True,
    )
    @app_commands.checks.cooldown(5, 5)
    @commands.cooldown(1, 30, commands.BucketType.category)
    @commands.max_concurrency(1, per=commands.BucketType.guild, wait=False)
    async def guild_auditlog(self, ctx: BaseContext) -> Optional[discord.Message]:
        """View your Audit Log!"""
        description: str = (
            "There are multiple options for you to choose from.\nEach option will give you access to the latest logs from specific events:"
            "\n\n<:Join:932976724235395072> ` - ` Members\n<:Join:932976724235395072> ` - ` Moderation"
            "\n<:Join:932976724235395072> ` - ` Emotes\n<:Join:932976724235395072> ` - ` Stickers\n<:Join:932976724235395072> ` - ` Messages"
        )

        audit_log_emb = BaseEmbed(
            title=f"{ctx.guild}'s Audit Log",
            description=description,
            colour=self.bot.colour,
        )
        message = await ctx.reply(
            f"Give me a second please <a:Load:1045668183434088479>",
            mention_author=False,
        )
        await asyncio.sleep(1)
        view = MainAuditLog(self.bot, ctx, message.id)
        view.message = await message.edit(
            content=None,
            embed=audit_log_emb,
            view=view,
            allowed_mentions=self.bot.mentions,
        )

    @guild.command(
        name="convertemote",
        brief="URL to Webhook",
        aliases=["ce"],
        with_app_command=True,
    )
    @app_commands.checks.cooldown(5, 5)
    @commands.has_guild_permissions(manage_webhooks=True)
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    @app_commands.checks.bot_has_permissions(manage_webhooks=True)
    async def guild_convertemote(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Enable to convert emote urls to webhooks."""
        query: str = (
            "INSERT INTO guild_settings VALUES ($1, $2) "
            "ON CONFLICT (guild_id) "
            "DO UPDATE SET convert_url_to_webhook = $2 WHERE guild_settings.guild_id = $1"
        )
        data = await self.bot.db.fetchval(
            "SELECT convert_url_to_webhook FROM guild_settings WHERE guild_id = $1",
            ctx.guild.id,
        )
        if data == True:
            await ctx.reply(
                f"I will hereby `not convert` emote urls sent to webhook messages in **{ctx.guild}** \U0001f91d"
            )
            await ctx.add_nanotick()
            self.bot.settings[ctx.guild.id]["convert_url_to_webhook"] = False
            return await self.bot.db.execute(query, ctx.guild.id, False)

        await ctx.reply(
            f"I will hereby `convert` emote urls sent to webhook messages in **{ctx.guild}** \U0001f91d"
        )
        await ctx.add_nanotick()
        self.bot.settings[ctx.guild.id]["convert_url_to_webhook"] = True
        await self.bot.db.execute(query, ctx.guild.id, True)

    @commands.hybrid_group(
        name="emote",
        brief="Emote Commands",
        aliases=["em", "emotes"],
        with_app_command=True,
    )
    @app_commands.describe(emote="Group commands for the guild's emotes.")
    async def emote_group(self, ctx: BaseContext):
        """Group commands for emotes present."""
        if ctx.invoked_subcommand is None:
            return await ctx.command_help()

    @emote_group.command(name="info", brief="Get emote info.", with_app_command=True)
    @app_commands.describe(emote="Select an emote.")
    @app_commands.autocomplete(emote=emote_name_autocomplete)
    async def emote_info(self, ctx: BaseContext, *, emote: discord.Emoji = None):
        """Get info on an emote."""
        if emote is None:
            emote_list: List[discord.Emoji] = [
                f"{emote} ─ [`{emote}`]({emote.url})\n" for emote in ctx.guild.emojis
            ]
            embed_list: List[BaseEmbed] = []
            while emote_list:
                emote_embs = BaseEmbed(
                    title=f"\U0001f4dc {ctx.guild}'s Emotes",
                    description="".join(emote_list[:10]),
                    colour=self.bot.colour,
                )
                try:
                    emote_embs.set_thumbnail(url=ctx.guild.icon.url)
                except AttributeError:
                    pass
                emote_embs.set_footer(
                    text=f"Invoked By : {ctx.author}",
                    icon_url=ctx.author.display_avatar.url,
                )
                emote_list = emote_list[10:]
                embed_list.append(emote_embs)
            return await Paginator(self.bot, ctx, embeds=embed_list).send(ctx)

        if emote:
            emote_emb = BaseEmbed(
                title="\U0001f4dc Emote Info",
                description=f"<:ReplyContinued:930634770004725821> **Emote Name :** `{emote.name}`\n<:ReplyContinued:930634770004725821> **From Guild :** `{emote.guild.name}`\n<:ReplyContinued:930634770004725821> **Emote ID :** [`{emote.id}`]({emote.url})\n<:Reply:930634822865547294> **Created On :**{self.bot.timestamp(emote.created_at, style='d')}",
                colour=self.bot.colour,
            )
            emote_emb.set_image(url=emote.url)
            emote_emb.set_footer(
                text=f"Invoked By : {ctx.author}",
                icon_url=ctx.author.display_avatar.url,
            )
            await ctx.send(embed=emote_emb)

    @emote_group.command(
        name="delete", brief="Delete emote.", aliases=["del"], with_app_command=True
    )
    @app_commands.autocomplete(emote=emote_name_autocomplete)
    @commands.has_permissions(manage_emojis_and_stickers=True)
    @app_commands.describe(emote="The emote you want to delete.")
    async def emote_delete(
        self, ctx: BaseContext, *, emote: discord.Emoji = None
    ) -> Optional[discord.Message]:
        """Delete an emote."""
        if emote.guild.id != ctx.guild.id:
            return await ctx.reply(
                f"**{ctx.author} - {emote} is not present in **{ctx.guild}**!"
            )

        async def yes(
            ui: discord.ui.View,
            interaction: discord.Interaction,
            button: discord.ui.Button,
        ):
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            try:
                await emote.delete(reason=f"{ctx.author} wanted to delete it.")
                return await ui.response.edit(
                    content=f"**{ctx.author}** - Successfully deleted the emote <:WorryPray:941747031356104734>",
                    view=ui,
                )
            except discord.errors.HTTPException:
                return await ui.response.edit(
                    f"**{ctx.author}** - I wasn't able to delete due to an error communicating with Discord <:Pain:911261018582306867>"
                )

        async def no(
            ui: discord.ui.View,
            interaction: discord.Interaction,
            button: discord.ui.Button,
        ):
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            return await ui.response.edit(
                content=f"Seems like I'm not deleting {emote}. Won't do it **{ctx.author}** <:DuckThumbsUp:917007413259956254>"
            )

        Confirmation.response = await ctx.reply(
            f"**{ctx.author}** - are you sure you want to delete {emote} - <:SIDGoesHmmMan:967421008137056276>",
            view=Confirmation(ctx, yes, no),
        )

    @emote_group.command(
        name="rename", brief="Rename emote.", aliases=["rn"], with_app_command=True
    )
    @app_commands.autocomplete(emote=emote_name_autocomplete)
    @commands.has_permissions(manage_emojis_and_stickers=True)
    @app_commands.describe(emote="The emote you want to rename.")
    @app_commands.describe(name="The name you want to edit it with.")
    async def emote_rename(
        self, ctx: BaseContext, emote: discord.Emoji = None, *, name: str
    ) -> Optional[discord.Message]:
        """Rename an emote."""
        if emote.guild.id != ctx.guild.id:
            return await ctx.reply(
                f"**{ctx.author} - {emote} is not present in **{ctx.guild}**!"
            )

        async def yes(
            ui: discord.ui.View,
            interaction: discord.Interaction,
            button: discord.ui.Button,
        ):
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            try:
                await emote.edit(name=name)
                return await ui.response.edit(
                    content=f"**{ctx.author}** - Successfully rename the emote to `{name}` <:WorryPray:941747031356104734>",
                    view=ui,
                )
            except discord.errors.HTTPException:
                return await ui.response.edit(
                    f"**{ctx.author}** - I wasn't able to rename due to an error communicating with Discord <:Pain:911261018582306867>"
                )

        async def no(
            ui: discord.ui.View,
            interaction: discord.Interaction,
            button: discord.ui.Button,
        ):
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            return await ui.response.edit(
                content=f"Seems like I'm not renaming {emote} to `{name}`. Won't do it **{ctx.author}** <:DuckThumbsUp:917007413259956254>"
            )

        Confirmation.response = await ctx.reply(
            f"**{ctx.author}** - are you sure you want to rename {emote} to `{name}` - <:SIDGoesHmmMan:967421008137056276>",
            view=Confirmation(ctx, yes, no),
        )

    @commands.hybrid_command(
        name="stickers", brief="Info on stickers", aliases=["stcki", "sticker"]
    )
    async def stickers(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Get information on each sticker present!"""
        if ctx.message.reference:
            try:
                sticker = await self.bot.fetch_sticker(
                    ctx.message.reference.resolved.stickers[0].id
                )
            except discord.HTTPException:
                return await ctx.reply(
                    f"Sorry **{ctx.author}**, there seems to be an issue in fetching the details of that sticker <:SIDGoesHmmMan:967421008137056276> Please try again <a:IWait:948253556190904371>"
                )
            referenced_sticker_emb = BaseEmbed(
                title=f"\U0001f4dc {ctx.guild}'s Sticker Info",
                description=f"<:ReplyContinued:930634770004725821> **ID** : [`{sticker.id}`]({sticker.url})\n<:ReplyContinued:930634770004725821> **Name** : `{sticker.name}`\n<:ReplyContinued:930634770004725821> **Created At** : {self.bot.timestamp(sticker.created_at, style='R')}\n<:Reply:930634822865547294> **Trigger Emote** : :{sticker.emoji}:",
                colour=self.bot.colour,
            )
            referenced_sticker_emb.set_image(url=sticker.url)
            referenced_sticker_emb.set_footer(
                text=f"Invoked By : {ctx.author}", icon_url=ctx.author.display_avatar
            )
            if sticker.description:
                referenced_sticker_emb.add_field(
                    name="Description", value=f">>> {sticker.description}"
                )
            return await ctx.send(embed=referenced_sticker_emb)

        if not ctx.guild.stickers:
            return await ctx.reply(f"**{ctx.guild}** - Has no stickers present.")

        if len(ctx.guild.stickers) == 1:
            for alpha in ctx.guild.stickers:
                single_sticker_emb = BaseEmbed(
                    title=f"\U0001f4dc {ctx.guild}'s Sticker Info",
                    description=f"<:ReplyContinued:930634770004725821> **ID** : [`{alpha.id}`]({alpha.url})\n<:ReplyContinued:930634770004725821> **Name** : `{alpha.name}`\n<:ReplyContinued:930634770004725821> **Created At** : {self.bot.timestamp(alpha.created_at, style='R')}\n<:Reply:930634822865547294> **Trigger Emote** : :{alpha.emoji}:",
                    colour=self.bot.colour,
                )
                single_sticker_emb.set_image(url=alpha.url)
                single_sticker_emb.set_footer(
                    text=f"Invoked By : {ctx.author}",
                    icon_url=ctx.author.display_avatar,
                )
                return await ctx.send(embed=single_sticker_emb)

        embed_list: List = []
        for beta in ctx.guild.stickers:
            sticker_embs = BaseEmbed(
                title=f"\U0001f4dc {ctx.guild}'s Sticker Info",
                description=f"<:ReplyContinued:930634770004725821> **ID** : [`{beta.id}`]({beta.url})\n<:ReplyContinued:930634770004725821> **Name** : `{beta.name}`\n<:ReplyContinued:930634770004725821> **Created At** : {self.bot.timestamp(beta.created_at, style='R')}\n<:Reply:930634822865547294> **Trigger Emote** : :{beta.emoji}:",
                colour=self.bot.colour,
            )
            if beta.description:
                sticker_embs.add_field(
                    name="Description", value=f">>> {beta.description}"
                )

            sticker_embs.set_image(url=beta.url)
            sticker_embs.set_footer(
                text=f"Invoked By : {ctx.author}", icon_url=ctx.author.display_avatar
            )
            try:
                sticker_embs.set_thumbnail(url=ctx.guild.icon.url)
            except AttributeError:
                pass
            embed_list.append(sticker_embs)
        return await Paginator(self.bot, ctx, embeds=embed_list).send(ctx)
