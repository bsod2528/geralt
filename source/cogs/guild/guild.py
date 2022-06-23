import discord
import asyncio
import asyncpg

from discord.ext import commands

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

    async def fetch_prefix(self, message: discord.Message):
        return tuple([prefix["guild_prefix"] for prefix in await self.bot.db.fetch("SELECT guild_prefix FROM custom_prefix WHERE guild_id = $1", message.guild.id)]) or self.bot.default_prefix

    async def dont_archive_and_delete(self, ctx: GeraltContext, ticket_id: int):
        await self.bot.db.execute("DELETE FROM ticket_kernel WHERE ticket_id = $1 AND guild_id = $2", ticket_id, ctx.guild.id)
        await ctx.add_nanotick()
        await asyncio.sleep(5)
        await ctx.channel.delete()

    async def archive_and_dont_delete(self, ctx: GeraltContext, ticket_id: int):
        await ctx.channel.edit(name = f"{ctx.channel.name} archived")

    @commands.group(
        name = "prefix",
        brief = "Prefix Related Sub-Commands",
        aliases = ["p"])
    @commands.guild_only()
    @commands.has_guild_permissions(administrator = True)
    @commands.has_guild_permissions(manage_channels = True)
    async def prefix(self, ctx: GeraltContext):
        if ctx.invoked_subcommand is None:
            try:
                current_prefix = self.bot.prefixes[ctx.guild.id]
            except KeyError:
                current_prefix = await self.bot.db.fetchval("SELECT (guild_prefix) FROM custom_prefix WHERE guild_id = $1", ctx.guild.id)
            if not current_prefix:
                current_prefix = self.bot.default_prefix
            prefix_emb = BaseEmbed(
                description = f"`{current_prefix}`\n`.g`\n{ctx.guild.me.mention}",
                colour = self.bot.colour)
            prefix_emb.set_footer(text = f"Run {ctx.clean_prefix}help prefix.")
            if ctx.guild.icon.url:
                prefix_emb.set_author(name = ctx.guild, icon_url = ctx.guild.icon.url)
            else:
                prefix_emb.set_author(name = ctx.guild)
            await ctx.reply(embed = prefix_emb, mention_author = False)

    @prefix.command(
        name = "set",
        brief = "Set Guild Prefix",
        aliases = ["s"])
    async def prefix_set(self, ctx: GeraltContext, *, prefix: str = None):
        """Add custom prefixes. However, the default one will not work."""
        try:
            if prefix == "--":
                return await ctx.reply(f"I'm afraid that `--` cannot be set as a guild prefix. As it is used for invoking flags. Try another one.")
            elif prefix is None:
                return await ctx.reply("You do realise you have to enter a `new prefix` for that to become the prefix for this guild?")
            elif len(prefix) > 15:
                return await ctx.reply("Your definitely going to ace that essay writing competition")
            else:
                await self.bot.db.execute("INSERT INTO custom_prefix (guild_prefix, guild_id, guild_name) VALUES ($1, $2, $3)", prefix, ctx.guild.id, ctx.guild.name)
                self.bot.prefixes[ctx.guild.id] = await self.fetch_prefix(ctx.message)
                await ctx.reply(f"**{ctx.message.author}** - my prefix for **{ctx.guild.name}** will here after be `{prefix}` <:SarahLaugh:907109900952420373>")
        
        except asyncpg.UniqueViolationError:
            await self.bot.db.execute("UPDATE custom_prefix SET guild_prefix = $1 WHERE guild_id = $2 AND guild_name = $3", prefix, ctx.guild.id, ctx.guild.name)
            await ctx.reply(f"**{ctx.message.author}** - my prefix for **{ctx.guild.name}** has been updated `{prefix}` <a:DuckPopcorn:917013065650806854>")
            self.bot.prefixes[ctx.guild.id] = await self.fetch_prefix(ctx.message)

    @prefix.command(
        name = "reset",
        brief = "Resets to default",
        aliases = ["r"])
    async def prefix_reset(self, ctx: GeraltContext):
        await self.bot.db.execute("DELETE FROM custom_prefix WHERE guild_id = $1 AND guild_name = $2", ctx.guild.id, ctx.guild.name)
        await ctx.reply(f"Reset prefix back to `{self.bot.default_prefix}` ")
        self.bot.prefixes[ctx.guild.id] = self.bot.default_prefix

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
    async def ticket(self, ctx : GeraltContext):
        """Take care of your server by utilising tickets."""
        if ctx.invoked_subcommand is None:
            await ctx.command_help()
    
    @ticket.command(
        name = "setup",
        brief = "Set-up ticket system.")
    async def ticket_setup(self, ctx: GeraltContext, *, channel: discord.TextChannel = None):
        """Setup ticket system in your server.
        ────
        **Args :** `channel` ─ `#channel` / `send the id` / `type the name`
        **Example :** `.gticket setup #channel / channel / 123456789012345678`"""
        if not channel:
            return await ctx.reply(f"To set up ticket system, you have to `mention` / `send the id` / `type the name of the channel` for me to send the main panel over there.")
        await TicketSetup(self.bot, ctx, channel).send()

    @ticket.command(
        name = "close",
        brief = "Close a ticket.")
    async def ticket_close(self, ctx: GeraltContext, ticket_id: int = None):
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
    async def ticket_status(self, ctx: GeraltContext):
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
    async def ticket_dismantle(self, ctx: GeraltContext):
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