import discord
import asyncio
import asyncpg as PSQL

from discord.ext import commands

from Source.Kernel.Views.Interface import Confirmation

class Guild(commands.Cog):
    """Guild Management Commands"""
    def __init__(self, bot):
        self.bot = bot

    async def fetch_prefix(self, message : discord.Message):
        return tuple([pre["guild_prefix"] for pre in await self.bot.db.fetch("SELECT guild_prefix FROM custom_prefix WHERE guild_id = $1", message.guild.id)]) or self.bot.default_prefix

    @commands.group(
        name = "data",
        brief = "DB Related Commands for Guild Admin",
        aliases = ["db"])
    @commands.guild_only()
    @commands.has_guild_permissions(administrator = True)
    async def data(self, ctx : commands.context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @data.command(
        name = "show",
        brief = "Shows Stored Information")
    async def show_info(self, ctx : commands.context):
        """Shows the entire information"""
        guild_deets = await self.bot.db.fetchval(f"SELECT (id, name, owner_id) FROM guild_info WHERE name = $1 AND id = $2", ctx.guild.name, ctx.guild.id)
        await ctx.send(content = f"""The following details have been stored :

>>> │ ` ─ ` Name : \"**{guild_deets[1]}**\" ─ (`{guild_deets[0]}`)\n│ ` ─ ` Owner : <@{guild_deets[2]}> ─ (`{guild_deets[2]}`")""", allowed_mentions = self.bot.mentions)

    @data.command(
        name = "clear",
        brief = "Delete Information.",
        aliases = ["cl"])
    async def clear_info(self, ctx : commands.context):
        """Deletes the information stored in database"""
        async def yes(ui : discord.ui.View, interaction : discord.Interaction, button : discord.ui.button, disabled : bool = True):
            if button.user != ctx.author:
                await interaction.response.send_message(content = "This is meant for **Guild Administrators** to interact with <a:PAIN:939876989655994488>", ephemeral = True)
            await ui.response.edit(content = f"As you wish, I will be deleting all the information of **{ctx.guild.name}** from my database <:DuckThumbsUp:917007413259956254>",  view = None, allowed_mentions = self.bot.mentions)
            button.disabled = True
            
            await self.bot.db.execute(f"DELETE FROM guild_info WHERE id = $1", ctx.guild.id)
            await asyncio.sleep(1) 
            await ui.response.edit(content = "Successfully deleted all the information <:Dayum:907110455095480340>", allowed_mentions = self.bot.Mention)
        
        async def no(ui : discord.ui.View, interaction : discord.Interaction, button : discord.ui.button, disabled : bool = True):
            if button.user != ctx.author:
                await interaction.response.send_message(content = "This is meant for **Guild Administrators** to interact with <a:PAIN:939876989655994488>", ephemeral = True)
            await ui.response.edit(content = "Okay <:HaroldSaysOkay:907110916104007681> Seems like you are okay with me storing the information.",  view = None, allowed_mentions = self.bot.mentions)
            button.disabled = True
        Confirmation.response = await ctx.reply("Are you sure you want to **delete** all the information stored in the database <:BallManHmm:933398958263386222>", view = Confirmation(yes, no), allowed_mentions = self.bot.mentions)

    @data.command(
        name = "add",
        brief = "Adds Information")
    async def add_info(self, ctx : commands.context):
        """Adds data back into the database"""
        async def yes(ui : discord.ui.View, interaction : discord.Interaction, button : discord.ui.button):
            if button.user != ctx.author:
                await interaction.response.send_message(content = "This is meant for **Guild Administrators** to interact with <a:PAIN:939876989655994488>", ephemeral = True)
            await ui.response.edit(content = f"As you wish, I will be adding all the information of **{ctx.guild.name}** from my database <:DuckThumbsUp:917007413259956254>", view = None, allowed_mentions = self.bot.mentions)
            await self.bot.DB.execute(f"INSERT INTO guild_info (id, name, owner_id) VALUES ($1, $2, $3)", ctx.guild.id, ctx.guild.name, ctx.guild.owner.id)
            await asyncio.sleep(1) 
            await ui.response.edit(content = "Successfully added all the information <:Dayum:907110455095480340>",  view = None, allowed_mentions = self.bot.Mention)
        
        async def no(ui : discord.ui.View, interaction : discord.Interaction, button : discord.ui.button, disabled : bool = True):
            if button.user != ctx.author:
                await interaction.response.send_message(content = "This is meant for **Guild Administrators** to interact with <a:PAIN:939876989655994488>", ephemeral = True)
            await ui.response.edit(content = f"Okay <:HaroldSaysOkay:907110916104007681> Seems like I'm not adding {ctx.guild.name}'s information today <:SarahThonk:907109849437982750>", allowed_mentions = self.bot.mentions)
            button.disabled = True
        Confirmation.response = await ctx.reply("Are you sure you want to **add** all the information stored in the database <:BallManHmm:933398958263386222>", view = Confirmation(yes, no), allowed_mentions = self.bot.mentions)

    @commands.group(
        name = "prefix",
        brief = "Prefix Related Sub-Commands",
        aliases = ["p"])
    @commands.guild_only()
    @commands.has_guild_permissions(administrator = True)
    async def prefix(self, ctx : commands.context):
        current_prefix = await self.bot.db.fetchval("SELECT (guild_prefix) FROM custom_prefix WHERE guild_id = $1", ctx.guild.id)
        await ctx.reply(f"My prefix for **{ctx.guild.name}** is `{current_prefix}` <:OkayDude:955454653900922901>")

    @prefix.command(
        name = "set",
        brief = "Set Guild Prefix",
        aliases = ["s"])
    async def prefix_set(self, ctx : commands.context, *, prefix : str = None):
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
    async def prefix_reset(self, ctx : commands.context):
        await self.bot.db.execute("DELETE FROM custom_prefix WHERE guild_id = $1 AND guild_name = $2", ctx.guild.id, ctx.guild.name)
        await ctx.reply(f"Reset prefix back to `{self.bot.default_prefix}` ")
        self.bot.prefixes[ctx.guild.id] = self.bot.default_prefix

async def setup(bot):
    await bot.add_cog(Guild(bot)) 