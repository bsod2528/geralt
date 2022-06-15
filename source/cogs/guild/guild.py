import discord
import asyncpg as PSQL

from discord.ext import commands

from ...kernel.subclasses.bot import Geralt
from ...kernel.subclasses.context import GeraltContext

class Guild(commands.Cog):
    """Manage the guild and my settings."""
    def __init__(self, bot : Geralt):
        self.bot = bot
    
    @property
    def emote(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name = "Guild", id = 917013065650806854, animated = True)   

    async def fetch_prefix(self, message : discord.Message):
        return tuple([prefix["guild_prefix"] for prefix in await self.bot.db.fetch("SELECT guild_prefix FROM custom_prefix WHERE guild_id = $1", message.guild.id)]) or self.bot.default_prefix

    @commands.group(
        name = "prefix",
        brief = "Prefix Related Sub-Commands",
        aliases = ["p"])
    @commands.guild_only()
    @commands.has_guild_permissions(administrator = True)
    async def prefix(self, ctx : GeraltContext):
        if ctx.invoked_subcommand is None:
            current_prefix = await self.bot.db.fetchval("SELECT (guild_prefix) FROM custom_prefix WHERE guild_id = $1", ctx.guild.id)
            if not current_prefix:
                current_prefix = self.bot.default_prefix
            await ctx.reply(f"My prefix for **{ctx.guild.name}** is `{current_prefix}` <:TokoOkay:898611996163985410>")

    @prefix.command(
        name = "set",
        brief = "Set Guild Prefix",
        aliases = ["s"])
    async def prefix_set(self, ctx : GeraltContext, *, prefix : str = None):
        """Add custom prefixes. However, the default one will not work."""
        try:
            if prefix == "--":
                await ctx.reply(f"I'm afraid that `--` cannot be set as a guild prefix. As it is used for invoking flags. Try another one.")
            elif prefix is None:
                await ctx.reply("You do realise you have to enter a `new prefix` for that to become the prefix for this guild?")
            else:
                await self.bot.db.execute("INSERT INTO custom_prefix (guild_prefix, guild_id, guild_name) VALUES ($1, $2, $3)", prefix, ctx.guild.id, ctx.guild.name)
                self.bot.prefixes[ctx.guild.id] = await self.fetch_prefix(ctx.message)
                await ctx.reply(f"**{ctx.message.author}** - my prefix for **{ctx.guild.name}** will here after be `{prefix}` <:SarahLaugh:907109900952420373>")
        
        except PSQL.UniqueViolationError:
            await self.bot.db.execute("UPDATE custom_prefix SET guild_prefix = $1 WHERE guild_id = $2 AND guild_name = $3", prefix, ctx.guild.id, ctx.guild.name)
            await ctx.reply(f"**{ctx.message.author}** - my prefix for **{ctx.guild.name}** has been updated `{prefix}` <a:DuckPopcorn:917013065650806854>")
            self.bot.prefixes[ctx.guild.id] = await self.fetch_prefix(ctx.message)

    @prefix.command(
        name = "reset",
        brief = "Resets to default",
        aliases = ["r"])
    async def prefix_reset(self, ctx : GeraltContext):
        await self.bot.db.execute("DELETE FROM custom_prefix WHERE guild_id = $1 AND guild_name = $2", ctx.guild.id, ctx.guild.name)
        await ctx.reply(f"Reset prefix back to `{self.bot.default_prefix}` ")
        self.bot.prefixes[ctx.guild.id] = self.bot.default_prefix