import asyncio
from code import interact
import asyncpg
import discord

from discord.ext import commands
from discord import app_commands
from typing import Optional, List

from ...kernel.subclasses.bot import Geralt
from ...kernel.views.meta import Confirmation
from ...kernel.subclasses.embed import BaseEmbed
from ...kernel.subclasses.context import GeraltContext
from ...kernel.views.tickets import CallTicket, TicketSetup

class Guild(commands.Cog):
    """Manage the guild and my settings."""
    def __init__(self, bot : Geralt):
        self.bot : Geralt = bot

        if not self.bot.persistent_views:
            self.bot.add_view(CallTicket(self.bot, GeraltContext))
    
    @property
    def emote(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name = "Guild", id = 917013065650806854, animated = True)   

    async def dont_archive_and_delete(self, ctx: GeraltContext, ticket_id: int):
        await self.bot.db.execute("DELETE FROM ticket_kernel WHERE ticket_id = $1 AND guild_id = $2", ticket_id, ctx.guild.id)
        await ctx.add_nanotick()
        await asyncio.sleep(5)
        await ctx.channel.delete()

    async def archive_and_dont_delete(self, ctx: GeraltContext, ticket_id: int):
        await ctx.channel.edit(name = f"{ctx.channel.name} archived")

    async def guild_preifx_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        tag_deets = await self.bot.db.fetch("SELECT UNNEST(guild_prefix) FROM prefix WHERE guild_id = $1", interaction.guild_id)
        names = [f"{deets[0]}" for deets in tag_deets]
        return [app_commands.Choice(name = names, value = names) for names in names if current.lower() in names]

    @commands.hybrid_group(
        name = "prefix",
        brief = "Prefix Related Sub-Commands",
        aliases = ["p"],
        with_app_command = True)
    @commands.guild_only()
    @commands.cooldown(3, 5, commands.BucketType.user)
    @commands.has_guild_permissions(manage_guild = True)
    @commands.has_guild_permissions(manage_roles = True)
    @commands.has_guild_permissions(administrator = True)
    @commands.has_guild_permissions(manage_channels = True)
    async def prefix(self, ctx: GeraltContext) -> Optional[discord.Message]:
        """Prefix related commands."""
        if ctx.invoked_subcommand is None:
            prefix_emb = BaseEmbed(
                description = f"\n".join(await self.bot.get_prefix(ctx.message)),
                colour = self.bot.colour)
            prefix_emb.set_footer(text = f"Run {ctx.clean_prefix}help prefix.")
            if ctx.guild.icon.url:
                prefix_emb.set_author(name = f"{len(await self.bot.get_prefix(ctx.message))} Prefixes ─ {ctx.guild}", icon_url = ctx.guild.icon.url)
            else:
                prefix_emb.set_author(name = ctx.guild)
            await ctx.reply(embed = prefix_emb, mention_author = False)

    @prefix.command(
        name = "add",
        brief = "Add Custom Prefixes",
        aliases = ["a"],
        with_app_command = True)
    @app_commands.checks.cooldown(3, 5)
    @commands.cooldown(3, 5, commands.BucketType.user)
    @app_commands.autocomplete(prefix = guild_preifx_autocomplete)
    @app_commands.describe(prefix = "Make sure you're not entering the same prefix as shown here!")
    async def prefix_add(self, ctx: GeraltContext, *, prefix: str = None):
        """Add a custom prefix.
        ────
        **Note:** Once a prefix is added, default prefix will not work \U0001f44d
        ────"""
        total_prefixes = await self.bot.get_prefix(ctx.message)
        if len(total_prefixes) > 14:
            return await ctx.reply(f"For **{ctx.guild}** ─ The maximum of `15` prefixes has reached. To add more, please remove other custom prefixes <:SarahYay:990543210235461682>")
        if prefix is None:
            return await ctx.reply("You do realise you have to enter a `new prefix` for that to become the prefix for this guild? <:SarahPout:989816223544012801>")
        if len(prefix) > 15:
            return await ctx.reply("You're definitely going to ace that essay writing competition. <:SarahLaugh:907109900952420373>")
        if prefix == "--":
            return await ctx.reply(f"I'm afraid that `--` cannot be set as a guild prefix. As it is used for invoking flags. Try another one.")
        try:
            query = "INSERT INTO prefix VALUES ($1, ARRAY [$2]) ON CONFLICT (guild_id) " \
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
        name = "remove",
        brief = "Remove a prefix.",
        aliases = ["del"],
        with_app_command = True)
    @app_commands.checks.cooldown(3, 5)
    @commands.cooldown(3, 5, commands.BucketType.user)
    @app_commands.autocomplete(prefix = guild_preifx_autocomplete)
    @app_commands.describe(prefix = "Give in the prefix you want to you remove.")
    async def prefix_remove(self, ctx: GeraltContext, *, prefix: str = None) -> Optional[discord.Message]:
        """Remove a custom prefix."""
        if not prefix:
            return await ctx.reply("Pass in a `prefix` for me to remove from the list.")
        try:
            fetched_prefixes = "\n".join(await self.bot.get_prefix(ctx.message or discord.Interaction.channel))
            if prefix.strip() not in fetched_prefixes:
                return await ctx.reply(f"`{prefix}` ─ is not in the guild's prefix list for **{ctx.guild}** <:SarahPout:989816223544012801>")
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
    
    @commands.group(
        name = "ticket",
        brief = "Ticket - Tool for you server.",
        aliases = ["tt", "tools"])
    @commands.guild_only()
    @commands.has_guild_permissions(administrator = True)
    @commands.has_guild_permissions(manage_channels = True)
    @commands.bot_has_guild_permissions(manage_channels = True)
    @commands.cooldown(3, 20, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.guild)
    async def ticket(self, ctx : GeraltContext) -> Optional[discord.Message]:
        """Take care of your server by utilising tickets."""
        if ctx.invoked_subcommand is None:
            await ctx.command_help()
    
    @ticket.command(
        name = "setup",
        brief = "Set-up ticket system.")
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
        name = "close",
        brief = "Close a ticket.")
    @commands.cooldown(3, 20, commands.BucketType.user)
    async def ticket_close(self, ctx: GeraltContext, ticket_id: int = None) -> Optional[discord.Message]:
        """Close a ticket."""
        if not ticket_id:
           return await ctx.reply(f"Please pass in the ticket_id to close it.")
        async def yes(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.Button):
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            await ui.response.edit(content = "Archiving this ticket.", view = ui, allowed_mentions = self.bot.mentions)
            await self.archive_and_dont_delete(ctx, ticket_id)
            await ui.response.edit(content = "Archived", view = ui, allowed_mentions = self.bot.mentions)
        async def no(ui: discord.ui.View, interaction: discord.Interaction, button: discord.ui.Button):
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            await ui.response.edit(content = f"{ctx.channel.mention} will be deleted in 5 seconds", view = ui, allowed_mentions = self.bot.mentions)
            await self.dont_archive_and_delete(ctx, ticket_id)
        Confirmation.response = await ctx.reply("Do you want to archive this ticket?", view = Confirmation(ctx, yes, no), mention_author = False)

    @ticket.command(
        name = "status",
        brief = "Status of ticket system.")
    @commands.cooldown(3, 5, commands.BucketType.user)
    async def ticket_status(self, ctx: GeraltContext) -> Optional[discord.Message]:
        """Returns the ticket system status for this guild."""
        try:
            system_status = [f"> │ ` ─ ` System ID : `{self.bot.ticket_init[ctx.guild.id][6]}`\n> │ ` ─ ` Category ID : `{self.bot.ticket_init[ctx.guild.id][0]}`\n> │ ` ─ ` Panel Message ID : [**{self.bot.ticket_init[ctx.guild.id][2]}**]({self.bot.ticket_init[ctx.guild.id][3]})"]
            if not system_status:
                return await ctx.reply(f"**{ctx.guild}** has not set up Ticket System. To setup, run `{ctx.clean_prefix}ticket`.")
        except KeyError:
            fetch_deets = await self.bot.db.fetch("SELECT * FROM ticket_init WHERE guild_id = $1", ctx.guild.id)
            system_status = [f"> │ ` ─ ` System ID : `{data['id']}`\n> │ ` ─ ` Category ID : `{data['category_id']}`\n> │ ` ─ ` Panel Message ID : [**{data['sent_message_id']}**]({data['jump_url']})" for data in fetch_deets]
            if not fetch_deets:
                return await ctx.reply(f"**{ctx.guild}** has not set up Ticket System. To setup, run `{ctx.clean_prefix}ticket`.")

        status_emb = BaseEmbed(
            title = f"{ctx.guild}'s Ticket System Status",
            description = "".join(system_status),
            colour = self.bot.colour)
        status_emb.set_thumbnail(url = ctx.guild.icon.url)
        await ctx.reply(embed = status_emb, mention_author = False)

    @ticket.command(
        name = "dismantle",
        brief = "Dismantles Ticket System.",
        aliases = ["delete", "remove", "clear"])
    @commands.cooldown(2, 10, commands.BucketType.user)
    async def ticket_dismantle(self, ctx: GeraltContext) -> Optional[discord.Message]:
        """Disables the ticket system in your guild if present."""        
        try:
            try:
                await self.bot.http.delete_message(self.bot.ticket_init[ctx.guild.id][1] , self.bot.ticket_init[ctx.guild.id][2])
            except KeyError:
                data = await self.bot.db.fetchval("SELECT (sent_channel_id, sent_message_id) FROM ticket_init WHERE guild_id = $1", ctx.guild.id)
                await self.bot.http.delete_message(data[0] , data[1])
            try:
                query_one = "DELETE FROM ticket_init WHERE guild_id = $1 "
                query_two = "DELETE FROM ticket_kernel WHERE guild_id = $1"
                await self.bot.db.execute(query_one, ctx.guild.id)
                await self.bot.db.execute(query_two, ctx.guild.id)
            except asyncpg.errors as error:
                return await ctx.send(f"```py\n{error}\n```")
            await ctx.reply(f"Successfully dismantled the `ticket system` from **{ctx.guild}**")
            await ctx.add_nanotick()
        except discord.errors.NotFound:
            return await ctx.reply("It seems you have already executed this command.")
        await ctx.add_nanotick()