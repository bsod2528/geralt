import aiohttp
import discord

from discord.ext import commands

from ...kernel.subclasses.embed import BaseEmbed
from ...kernel.subclasses.bot import CONFIG, Geralt
from ...kernel.subclasses.context import GeraltContext

class Events(commands.Cog):
    def __init__(self, bot: Geralt):
        self.bot: Geralt = bot

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Invokes command [if needed] on editing a message"""
        if after.content == before.content:
            return  
        else:
            return await self.bot.process_commands(after)
    
    @commands.Cog.listener()
    async def on_command_completion(self, ctx: GeraltContext):
        command_name = ctx.command.root_parent
        if not command_name:
            command_name = ctx.command or ctx.invoked_subcommand
        if not ctx.guild:
            pass
        else:
                query = "INSERT INTO meta ("\
                        "command_name, guild_id, invoked_at, uses)" \
                        "VALUES ($1, $2, $3, 1)" \
                        "ON CONFLICT(command_name, guild_id)" \
                        "DO UPDATE SET uses = meta.uses + 1, invoked_at = $3, command_name = $1"
                await self.bot.db.execute(query, str(command_name), ctx.guild.id, ctx.message.created_at)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """Sends a Webhook upon joining a guild""" 
        join_emb = BaseEmbed(
            title = f":scroll: I Joined {guild.name}",
            colour = self.bot.colour)
        join_emb.add_field(
            name = "<:GeraltRightArrow:904740634982760459> General Information :",
            value = f"> ` ─ ` <a:Owner:905750348457738291> Owner : **{guild.owner}** (`{guild.owner.id}`) \n" \
                    f"> ` ─ ` <a:Info:905750331789561856> Identification No. : `{guild.id}` \n" \
                    f"> ` ─ ` <a:Verify:905748402871095336> Verification Level : {str(guild.verification_level).replace('_', ' ').replace('`None`', '`Nill`').title()}")
        join_emb.add_field(
            name = "<:GeraltRightArrow:904740634982760459> Initialisation :",
            value = f"> ` ─ ` <a:Woo:905754435379163176> Made On : {self.bot.timestamp(guild.created_at)} \n" \
                    f"> ` ─ ` <a:WumpusVibe:905457020575031358> I Joined : {self.bot.timestamp(discord.utils.utcnow())}",
            inline = False)                
        async with aiohttp.ClientSession() as session:
            join_log_webhook = discord.Webhook.partial(id = CONFIG.get("JOIN_LOG_ID"), token = CONFIG.get("JOIN_LOG_TOKEN"), session = session)
            await join_log_webhook.send(embed = join_emb)
            await join_log_webhook.session.close()
            await session.close()
    
    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        """Sends a Webhook upon being removed from a guild"""    
        leave_emb = BaseEmbed(
            title = f":scroll: I Left {guild.name}",
            colour = discord.Colour.from_rgb(255, 97, 142))
        leave_emb.add_field(
            name = "<:GeraltRightArrow:904740634982760459> General Information :",
            value = f"> ` ─ ` <a:Owner:905750348457738291> Owner : **{guild.owner}** (`{guild.owner.id}`) \n" \
                    f"> ` ─ ` <a:Info:905750331789561856> Identification No. : `{guild.id}` \n" \
                    f"> ` ─ ` <a:Verify:905748402871095336> Verification Level : {str(guild.verification_level).replace('_', ' ').replace('`None`', '`Nill`').title()} \n")
        leave_emb.add_field(
            name = "<:GeraltRightArrow:904740634982760459> Initialisation :",
            value = f"> ` ─ ` <a:Woo:905754435379163176> Made On : {self.bot.timestamp(guild.created_at)} \n" \
                    f"> ` ─ ` <a:PAIN:939876989655994488> I Left : {self.bot.timestamp(discord.utils.utcnow())}",
            inline = False)                
        async with aiohttp.ClientSession() as session:
            leave_log_webhook = discord.Webhook.partial(id = CONFIG.get("LEAVE_LOG_ID"), token = CONFIG.get("LEAVE_LOG_TOKEN"), session = session)
            await leave_log_webhook.send(embed = leave_emb)
            await leave_log_webhook.session.close()