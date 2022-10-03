import asyncio
import asyncpg
import discord

from discord.ext import commands
from discord import app_commands
from typing import Optional, List

from ...kernel.views.prefix import Prefix
from ...kernel.subclasses.bot import Geralt
from ...kernel.views.meta import Confirmation
from ...kernel.views.paginator import Paginator
from ...kernel.subclasses.embed import BaseEmbed
from ...kernel.subclasses.context import GeraltContext
from ...kernel.views.tickets import CallTicket, TicketSetup
from ...kernel.views.verification import SetupVerification, VerificationCall


class Guild(commands.Cog):
    """Manage the guild and my settings."""

    def __init__(self, bot: Geralt):
        self.bot: Geralt = bot

        if not self.bot.persistent_views:
            self.bot.add_view(CallTicket(self.bot, GeraltContext))
            self.bot.add_view(VerificationCall(self.bot, GeraltContext))

    @property
    def emote(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(
            name="Guild",
            id=917013065650806854,
            animated=True)

    async def dont_archive_and_delete(self, ctx: GeraltContext, ticket_id: int):
        await self.bot.db.execute("DELETE FROM ticket_kernel WHERE ticket_id = $1 AND guild_id = $2", ticket_id, ctx.guild.id)
        await ctx.add_nanotick()
        await asyncio.sleep(5)
        await ctx.channel.delete()

    async def archive_and_dont_delete(self, ctx: GeraltContext, ticket_id: int):
        await ctx.channel.edit(name=f"{ctx.channel.name} archived")

    async def guild_preifx_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        tag_deets = await self.bot.db.fetch("SELECT UNNEST(guild_prefix) FROM prefix WHERE guild_id = $1", interaction.guild_id)
        names = [f"{deets[0]}" for deets in tag_deets]
        return [app_commands.Choice(name=names, value=names)
                for names in names if current.lower() in names]

    @commands.hybrid_group(
        name="prefix",
        brief="Prefix Related Sub-Commands",
        aliases=["p"],
        with_app_command=True)
    @commands.guild_only()
    @commands.cooldown(3, 5, commands.BucketType.user)
    @commands.has_guild_permissions(manage_guild=True)
    @commands.has_guild_permissions(manage_roles=True)
    @commands.has_guild_permissions(administrator=True)
    @commands.has_guild_permissions(manage_channels=True)
    async def prefix(self, ctx: GeraltContext) -> Optional[discord.Message]:
        """Prefix related commands."""
        if ctx.invoked_subcommand is None:
            prefix_emb = BaseEmbed(
                description=f"> <:GeraltRightArrow:904740634982760459> " + "\n> <:GeraltRightArrow:904740634982760459> ".join(await self.bot.get_prefix(ctx.message)),
                colour=self.bot.colour)
            prefix_emb.set_footer(text=f"Run {ctx.clean_prefix}help prefix.")
            if ctx.guild.icon.url:
                prefix_emb.set_author(name=f"{len(await self.bot.get_prefix(ctx.message))} Prefixes ─ {ctx.guild}", icon_url=ctx.guild.icon.url)
            else:
                prefix_emb.set_author(name=ctx.guild)
            prefix_view = Prefix(self.bot, ctx)
            prefix_view.message = await ctx.reply(embed=prefix_emb, view=prefix_view, mention_author=False)

    @prefix.command(
        name="add",
        brief="Add Custom Prefixes",
        aliases=["a"],
        with_app_command=True)
    @app_commands.checks.cooldown(3, 5)
    @commands.cooldown(3, 5, commands.BucketType.user)
    @app_commands.autocomplete(prefix=guild_preifx_autocomplete)
    @app_commands.describe(
        prefix="Make sure you're not entering the same prefix as shown here!")
    async def prefix_add(self, ctx: GeraltContext, *, prefix: str = None):
        """Add a custom prefix."""
        total_prefixes = await self.bot.get_prefix(ctx.message)
        if prefix.strip() == ".g":
            return await ctx.reply(f"**{ctx.author}** - `.g` is the default prefix, so you can't add that lmao <:SarahLaugh:907109900952420373>")
        if len(total_prefixes) > 14:
            return await ctx.reply(f"For **{ctx.guild}** - The maximum of `15` prefixes has reached. To add more, please remove other custom prefixes <:SarahYay:990543210235461682>")
        if prefix is None:
            return await ctx.reply("You do realise you have to enter a `new prefix` for that to become the prefix for this guild? <:SarahPout:989816223544012801>")
        if len(prefix) > 15:
            return await ctx.reply("You're definitely going to ace that essay writing competition <:SarahLaugh:907109900952420373>")
        if prefix == "--":
            return await ctx.reply(f"I'm afraid that `--` cannot be set as a guild prefix. As it is used for invoking flags. Try another one.")
        try:
            fetched_data = await self.bot.db.fetch("SELECT UNNEST(guild_prefix) FROM prefix WHERE guild_id = $1", ctx.guild.id)
            for present_prefixes in fetched_data:
                if prefix in str(present_prefixes):
                    return await ctx.send(f"{prefix} is already present")
            query = "INSERT INTO prefix VALUES ($1, ARRAY [$2, '.g']) ON CONFLICT (guild_id) " \
                    "DO UPDATE SET guild_prefix = ARRAY_APPEND(prefix.guild_prefix, $2) WHERE prefix.guild_id = $1"
            await self.bot.db.execute(query, ctx.guild.id, prefix)
            data = await self.bot.db.fetch("SELECT guild_id, guild_prefix FROM prefix")
            for guild_id, prefixes in data:
                self.bot.prefixes[guild_id] = set(prefixes)
            await ctx.reply(f"**{ctx.message.author}** - `{prefix}` has been added to my prefix list for **{ctx.guild.name}** <:SarahLaugh:907109900952420373>")
        except Exception as exception:
            await ctx.add_nanocross()
            return await ctx.send(f"```py\n{exception}\n```")

    @prefix.command(
        name="remove",
        brief="Remove a prefix.",
        aliases=["del"],
        with_app_command=True)
    @app_commands.checks.cooldown(3, 5)
    @commands.cooldown(3, 5, commands.BucketType.user)
    @app_commands.autocomplete(prefix=guild_preifx_autocomplete)
    @app_commands.describe(prefix="Give in the prefix you want to you remove.")
    async def prefix_remove(self, ctx: GeraltContext, *, prefix: str = None) -> Optional[discord.Message]:
        """Remove a custom prefix."""
        if prefix.strip() == ".g":
            return await ctx.reply(f"**{ctx.author}** - `.g` is the default prefix, so you can't remove that lmao <:SarahLaugh:907109900952420373>")
        if not prefix:
            return await ctx.reply("Pass in a `prefix` for me to remove from the list.")
        try:
            fetched_prefixes = "\n".join(await self.bot.get_prefix(ctx.message or discord.Interaction.channel))
            if prefix.strip() not in fetched_prefixes:
                return await ctx.reply(f"`{prefix}` - is not in the guild's prefix list for **{ctx.guild}** <:SarahPout:989816223544012801>")
            query = "UPDATE prefix SET guild_prefix = ARRAY_REMOVE(prefix.guild_prefix, $2) WHERE guild_id = $1"
            await self.bot.db.execute(query, ctx.guild.id, prefix)
            data = await self.bot.db.fetch("SELECT guild_id, guild_prefix FROM prefix")
            for guild_id, prefixes in data:
                self.bot.prefixes[guild_id] = set(prefixes)
            await ctx.add_nanotick()
            await ctx.reply(f"**{ctx.message.author}** - `{prefix}` has been removed to my prefix list for **{ctx.guild.name}** <:SarahLaugh:907109900952420373>")
        except Exception as exception:
            await ctx.add_nanocross()
            return await ctx.send(f"```py\n{exception}\n```")

    @prefix.command(
        name="reset",
        brief="Reset all custom prefixes",
        with_app_command=True)
    @app_commands.checks.cooldown(3, 5)
    async def prefix_reset(self, ctx: GeraltContext):
        """Reset all the prefixes back to `.g`"""
        data = await self.bot.db.fetch("SELECT UNNEST(guild_prefix) FROM prefix WHERE guild_id = $1", ctx.guild.id)
        self.bot.prefixes[ctx.guild.id] = {".g", }
        await ctx.send(f"Reset all the `{len(data)}` prefixes back to `.g`.")
        await ctx.add_nanotick()
        return await self.bot.db.execute("DELETE FROM prefix WHERE guild_id = $1", ctx.guild.id)

    @commands.group(
        name="ticket",
        brief="Ticket - Tool for you server.",
        aliases=["tt", "tools"])
    @commands.guild_only()
    @commands.cooldown(3, 20, commands.BucketType.user)
    @commands.has_guild_permissions(administrator=True)
    @commands.has_guild_permissions(manage_channels=True)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def ticket(self, ctx: GeraltContext) -> Optional[discord.Message]:
        """Ticketing system for support in your guild."""
        if ctx.invoked_subcommand is None:
            await ctx.command_help()

    @ticket.command(
        name="setup",
        brief="Set-up ticket system.")
    @commands.max_concurrency(1, commands.BucketType.guild)
    async def ticket_setup(self, ctx: GeraltContext, *, channel: discord.TextChannel = None) -> Optional[discord.Message]:
        """Setup ticket system in your server.
        ────
        **Example :**
        `.gticket setup #channel / channel / 123456789012345678`
        ────"""
        if not channel:
            return await ctx.reply(f"To set up ticket system, you have to `mention` / `send the id` / `type the name of the channel` for me to send the main panel over there.")
        await TicketSetup(self.bot, ctx, channel).send()

    @ticket.command(
        name="close",
        brief="Close a ticket.")
    @commands.cooldown(3, 20, commands.BucketType.user)
    async def ticket_close(self, ctx: GeraltContext, ticket_id: int = None) -> Optional[discord.Message]:
        """Close a ticket."""
        if not ticket_id:
            return await ctx.reply(f"Please pass in the ticket_id to close it.")

        async def yes(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.Button):
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            await ui.response.edit(content="Archiving this ticket.", view=ui, allowed_mentions=self.bot.mentions)
            await self.archive_and_dont_delete(ctx, ticket_id)
            await ui.response.edit(content="Archived", view=ui, allowed_mentions=self.bot.mentions)

        async def no(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.Button):
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            await ui.response.edit(content=f"{ctx.channel.mention} will be deleted in 5 seconds", view=ui, allowed_mentions=self.bot.mentions)
            await self.dont_archive_and_delete(ctx, ticket_id)
        Confirmation.response = await ctx.reply("Do you want to archive this ticket?", view=Confirmation(ctx, yes, no), mention_author=False)

    @ticket.command(
        name="status",
        brief="Status of ticket system.")
    @commands.cooldown(3, 5, commands.BucketType.user)
    async def ticket_status(self, ctx: GeraltContext) -> Optional[discord.Message]:
        """Returns the ticket system status for this guild."""
        try:
            system_status = [
                f"> │ ` ─ ` System ID : `{self.bot.ticket_init[ctx.guild.id][6]}`\n> │ ` ─ ` Category ID : `{self.bot.ticket_init[ctx.guild.id][0]}`\n> │ ` ─ ` Panel Message ID : [**{self.bot.ticket_init[ctx.guild.id][2]}**]({self.bot.ticket_init[ctx.guild.id][3]})"]
            if not system_status:
                return await ctx.reply(f"**{ctx.guild}** has not set up Ticket System. To setup, run `{ctx.clean_prefix}ticket`.")
        except KeyError:
            fetch_deets = await self.bot.db.fetch("SELECT * FROM ticket_init WHERE guild_id = $1", ctx.guild.id)
            system_status = [
                f"> │ ` ─ ` System ID : `{data['id']}`\n> │ ` ─ ` Category ID : `{data['category_id']}`\n> │ ` ─ ` Panel Message ID : [**{data['sent_message_id']}**]({data['jump_url']})" for data in fetch_deets]
            if not fetch_deets:
                return await ctx.reply(f"**{ctx.guild}** has not set up Ticket System. To setup, run `{ctx.clean_prefix}ticket`.")

        status_emb = BaseEmbed(
            title=f"{ctx.guild}'s Ticket System Status",
            description="".join(system_status),
            colour=self.bot.colour)
        status_emb.set_thumbnail(url=ctx.guild.icon.url)
        await ctx.reply(embed=status_emb, mention_author=False)

    @ticket.command(
        name="dismantle",
        brief="Dismantles Ticket System.",
        aliases=["delete", "remove", "clear"])
    @commands.cooldown(2, 10, commands.BucketType.user)
    async def ticket_dismantle(self, ctx: GeraltContext) -> Optional[discord.Message]:
        """Disables the ticket system in your guild if present."""
        async def yes(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.Button):
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            try:
                try:
                    cache = self.bot.ticket_init[ctx.guild.id]
                    await self.bot.http.delete_message(cache[1], cache[2])
                except KeyError:
                    channel = await self.bot.db.fetchval("SELECT sent_channel_id FROM ticket_init WHERE guild_id = $1", ctx.guild.id)
                    message = await self.bot.db.fetchval("SELECT sent_message_id FROM ticket_init WHERE guild_id = $1", ctx.guild.id)
                    await self.bot.http.delete_message(channel, message)
                try:
                    query_one = "DELETE FROM ticket_init WHERE guild_id = $1 "
                    query_two = "DELETE FROM ticket_kernel WHERE guild_id = $1"
                    await self.bot.db.execute(query_one, ctx.guild.id)
                    await self.bot.db.execute(query_two, ctx.guild.id)
                except asyncpg.errors as error:
                    return await ui.response.edit(content=f"```py\n{error}\n```", view=ui, allowed_mentions=self.bot.mentions)
                await ui.response.edit(content=f"Successfully dismantled the `ticket system` from **{ctx.guild}**", view=ui, allowed_mentions=self.bot.mentions)
                await ctx.add_nanotick()
            except discord.errors.NotFound:
                return await ui.response.edit(content="It seems you have already executed this command.", view=ui, allowed_mentions=self.bot.mentions)
            await ctx.add_nanotick()

        async def no(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.Button):
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            await ui.response.edit(content="Seems like I'm not dismantling the ticket-system", view=ui, allowed_mentions=self.bot.mentions)
        Confirmation.response = await ctx.reply("Are you sure you want to dismantle the ticket-system?", view=Confirmation(ctx, yes, no), mention_author=False)

    @commands.group(
        name="verification",
        brief="Verification commands",
        aliases=["verify", "vf"])
    @commands.guild_only()
    @commands.cooldown(3, 20, commands.BucketType.user)
    @commands.has_guild_permissions(administrator=True)
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def verification(self, ctx: GeraltContext) -> Optional[discord.Message]:
        """Group commands for securing your guild."""
        if ctx.invoked_subcommand is None:
            return await ctx.command_help()

    @verification.command(
        name="setup",
        brief="Setup")
    async def verification_setup(self, ctx: GeraltContext, channel: Optional[discord.TextChannel]) -> Optional[discord.Message]:
        """Secure your guild with verification."""
        if ctx.guild.id in self.bot.verification:
            return await ctx.reply(f"**{ctx.author}** - verification system has already been setup here smh <a:ImSorryWhat:923941819266527304>. Run `{ctx.clean_prefix}verification status`")
        if not channel:
            return await ctx.reply(f"**{ctx.author}** - please `mention`, or send `channel id`, or `type the channel name` to setup the verification system.")
        await SetupVerification(self.bot, ctx, channel).send()

    @verification.command(
        name="dismantle",
        brief="Remove verification system",
        aliases=["remove"])
    async def verification_dismantle(self, ctx: GeraltContext):
        """Remove the verification system from your server."""
        async def yes(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.Button):
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            try:
                query = "DELETE FROM verification WHERE guild_id = $1"
                try:
                    cache = self.bot.verification[ctx.guild.id]
                    await self.bot.http.delete_message(cache[3], cache[4])
                except KeyError:
                    channel = await self.bot.db.fetchval("SELECT channel_id FROM verification WHERE guild_id = $1", ctx.guild.id)
                    message = await self.bot.db.fetchval("SELECT message_id FROM verification WHERE guild_id = $1", ctx.guild.id)
                    await self.bot.http.delete_message(channel, message)
                await self.bot.db.execute(query, ctx.guild.id)
                self.bot.verification.pop(ctx.guild.id)
            except Exception:
                await ctx.add_nanocross()
                await ui.response.edit(content=f"Verification system hasn't been set-up for **{ctx.guild}**.", view=ui, allowed_mentions=self.bot.mentions)
                return
            await ctx.add_nanotick()
            await ui.response.edit(content=f"Successfully removed the verification system for **{ctx.guild}**.", view=ui, allowed_mentions=self.bot.mentions)
            return

        async def no(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.Button):
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            await ui.response.edit(content=f"Alright, I am not dismantling the verification system here.", view=ui, allowed_mentions=self.bot.mentions)
        Confirmation.response = await ctx.reply("Are you sure you want to dismantle the verification system?", view=Confirmation(ctx, yes, no), mention_author=False)

    @verification.command(
        name="status",
        brief="Verification Status")
    async def verification_status(self, ctx: GeraltContext):
        """Returns verification status for your guild."""
        try:
            cache = self.bot.verification[ctx.guild.id]
            status = [
                f"> <:One:989876071052750868>**Question:**\n> {cache[0]}\n────\n> <:Two:989876145291948122> **Answer:**\n> {cache[1]}\n────\n> <:Three:989876184420610099>**Present In:**\n> <#{cache[3]}>"]
        except KeyError:
            data = await self.bot.db.fetch("SELECT * FROM verification WHERE guild_id = $1", ctx.guild.id)
            status = [
                f"> <:One:989876071052750868>**Question:**\n> {deets[1]}\n────\n> <:Two:989876145291948122> **Answer:**\n> {deets[2]}\n────\n> <:Three:989876184420610099>**Present In:**\n> <#{deets[4]}>" for deets in data]
        if not status:
            return await ctx.reply(f"**{ctx.author}** - verification system hasn't been setup for `{ctx.guild}`. Please run `{ctx.clean_prefix}help verification` for more information.")
        verification_status_emb = BaseEmbed(
            title=f"Verification Status for {ctx.guild}",
            description="".join(status),
            colour=self.bot.colour)
        verification_status_emb.set_footer(
            text=f"Run {ctx.clean_prefix}help verification.",
            icon_url=ctx.author.display_avatar)
        try:
            verification_status_emb.set_thumbnail(url=ctx.guild.icon.url)
        except AttributeError:
            pass
        await ctx.send(embed=verification_status_emb)

    @commands.hybrid_group(
        name="guild",
        brief="Guild Settings",
        with_app_command=True)
    @commands.guild_only()
    async def guild(self, ctx: GeraltContext):
        """Sub-commands for basic guild settings"""
        if ctx.invoked_subcommand is None:
            return await ctx.command_help()

    @guild.command(
        name="convertemote",
        brief="URL to Webhook",
        aliases=["ce"],
        with_app_command=True)
    @app_commands.checks.cooldown(5, 5)
    @commands.has_guild_permissions(manage_webhooks=True)
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    @app_commands.checks.bot_has_permissions(manage_webhooks=True)
    async def guild_convertemote(self, ctx: GeraltContext):
        """Enable to convert emote urls to webhooks."""
        # The boolean was originally set as a `boolean` in the postgre table.
        # Since I was unable to iterate through `boolean` values for the sake
        # of caching I converted them back into strings.
        query = "INSERT INTO guild_settings VALUES ($1, $2) " \
                "ON CONFLICT (guild_id) " \
                "DO UPDATE SET convert_url_to_webhook = $2 WHERE guild_settings.guild_id = $1"
        data = await self.bot.db.fetchval("SELECT convert_url_to_webhook FROM guild_settings WHERE guild_id = $1", ctx.guild.id)
        if data == "true":
            await ctx.reply(f"I will hereby `not convert` emote urls sent to webhook messages in **{ctx.guild}** \U0001f91d")
            await ctx.add_nanotick()
            self.bot.convert_url_to_webhook[ctx.guild.id] = "false"
            return await self.bot.db.execute(query, ctx.guild.id, "false")

        await ctx.reply(f"I will hereby `convert` emote urls sent to webhook messages in **{ctx.guild}** \U0001f91d")
        await ctx.add_nanotick()
        self.bot.convert_url_to_webhook[ctx.guild.id] = "true"
        await self.bot.db.execute(query, ctx.guild.id, "true")

    @commands.hybrid_command(
        name="emote",
        brief="Emote Info",
        aliases=["em", "emotes"],
        with_app_command=True)
    @app_commands.describe(emote="Get information on the emote you mention")
    async def emotes(self, ctx: GeraltContext, *, emote: commands.EmojiConverter = None):
        """Get info on emotes."""
        if emote is None:
            emote_list: List = [f"{emote} ─ [`{emote}`]({emote.url})\n" for emote in ctx.guild.emojis]
            embed_list: List = []
            while emote_list:
                emote_embs = BaseEmbed(
                    title=f"\U0001f4dc {ctx.guild}'s Emotes",
                    description="".join(emote_list[:10]),
                    colour=self.bot.colour)
                try:
                    emote_embs.set_thumbnail(url=ctx.guild.icon.url)
                except AttributeError:
                    pass
                emote_embs.set_footer(text=f"Invoked By : {ctx.author}", icon_url=ctx.author.display_avatar.url)
                emote_list = emote_list[10:]
                embed_list.append(emote_embs)
            return await Paginator(self.bot, ctx, embeds=embed_list).send(ctx)

        if emote:
            emote_emb = BaseEmbed(
                title="\U0001f4dc Emote Info",
                description=f"<:ReplyContinued:930634770004725821> **Emote Name :** `{emote.name}`\n<:ReplyContinued:930634770004725821> **From Guild :** `{emote.guild.name}`\n<:ReplyContinued:930634770004725821> **Emote ID :** [`{emote.id}`]({emote.url})\n<:Reply:930634822865547294> **Created On :**{self.bot.timestamp(emote.created_at, style='d')}",
                colour=self.bot.colour)
            emote_emb.set_image(url=emote.url)
            emote_emb.set_footer(text=f"Invoked By : {ctx.author}", icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=emote_emb)

    @commands.hybrid_command(
        name="stickers",
        brief="Info on stickers",
        aliases=["stcki", "sticker"])
    async def stickers(self, ctx: GeraltContext):
        """Get information on each sticker present!"""
        if ctx.message.reference:
            try:
                sticker = await self.bot.fetch_sticker(ctx.message.reference.resolved.stickers[0].id)
            except discord.HTTPException:
                return await ctx.reply(f"Sorry **{ctx.author}**, there seems to be an issue in fetching the details of that sticker <:SIDGoesHmmMan:967421008137056276> Please try again <a:IWait:948253556190904371>")
            referenced_sticker_emb = BaseEmbed(
                title=f"\U0001f4dc {ctx.guild}'s Sticker Info",
                description=f"<:ReplyContinued:930634770004725821> **ID** : [`{sticker.id}`]({sticker.url})\n<:ReplyContinued:930634770004725821> **Name** : `{sticker.name}`\n<:ReplyContinued:930634770004725821> **Created At** : {self.bot.timestamp(sticker.created_at, style='R')}\n<:Reply:930634822865547294> **Trigger Emote** : `{sticker.emoji}`",
                colour=self.bot.colour)
            referenced_sticker_emb.set_image(url=sticker.url)
            referenced_sticker_emb.set_footer(text=f"Invoked By : {ctx.author}", icon_url=ctx.author.display_avatar)
            if sticker.description:
                referenced_sticker_emb.add_field(
                    name="Description",
                    value=f">>> {sticker.description}")
            return await ctx.send(embed=referenced_sticker_emb)

        if not ctx.guild.stickers:
            return await ctx.reply(f"**{ctx.guild}** - Has no stickers present.")

        if len(ctx.guild.stickers) == 1:
            for alpha in ctx.guild.stickers:
                single_sticker_emb = BaseEmbed(
                    title=f"\U0001f4dc {ctx.guild}'s Sticker Info",
                    description=f"<:ReplyContinued:930634770004725821> **ID** : [`{alpha.id}`]({alpha.url})\n<:ReplyContinued:930634770004725821> **Name** : `{alpha.name}`\n<:ReplyContinued:930634770004725821> **Created At** : {self.bot.timestamp(alpha.created_at, style='R')}\n<:Reply:930634822865547294> **Trigger Emote** : `{alpha.emoji}`",
                    colour=self.bot.colour)
                single_sticker_emb.set_image(url=alpha.url)
                single_sticker_emb.set_footer(text=f"Invoked By : {ctx.author}", icon_url=ctx.author.display_avatar)
                return await ctx.send(embed=single_sticker_emb)

        embed_list: List = []
        for beta in ctx.guild.stickers:
            sticker_embs = BaseEmbed(
                title=f"\U0001f4dc {ctx.guild}'s Sticker Info",
                description=f"<:ReplyContinued:930634770004725821> **ID** : [`{beta.id}`]({beta.url})\n<:ReplyContinued:930634770004725821> **Name** : `{beta.name}`\n<:ReplyContinued:930634770004725821> **Created At** : {self.bot.timestamp(beta.created_at, style='R')}\n<:Reply:930634822865547294> **Trigger Emote** : `{beta.emoji}`",
                colour=self.bot.colour)
            if beta.description:
                sticker_embs.add_field(
                    name="Description",
                    value=f">>> {beta.description}")

            sticker_embs.set_image(url=beta.url)
            sticker_embs.set_footer(text=f"Invoked By : {ctx.author}", icon_url=ctx.author.display_avatar)
            try:
                sticker_embs.set_thumbnail(url=ctx.guild.icon.url)
            except AttributeError:
                pass
            embed_list.append(sticker_embs)
        return await Paginator(self.bot, ctx, embeds=embed_list).send(ctx)
