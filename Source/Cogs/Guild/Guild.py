import disnake
import asyncio
import asyncpg as PSQL

from disnake.ext import commands

from Source.Kernel.Views.Interface import Confirmation

class Guild(commands.Cog):
    """Guild Management Commands"""
    def __init__(self, bot):
        self.bot    =   bot

    @commands.group(
        name    =   "data",
        aliases =   ["db"],
        brief   =   "DB Related Commands for Guild Admin")
    @commands.has_guild_permissions(administrator = True)
    async def data(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)
    
    @data.command(
        name    =   "show",
        brief   =   "Shows Stored Information")
    async def show_info(self, ctx):
        """Shows the entire information"""
        GUILD_ID    =   await self.bot.DB.fetchval("SELECT * FROM guild_info WHERE id = $1", ctx.guild.id)
        OWNER_ID    =   await self.bot.DB.fetchval("SELECT * FROM guild_info WHERE owner_id = $1", ctx.guild.owner.id)
        SHOW_EMB    =   disnake.Embed(
            title   =   f"{ctx.guild.name}",
            colour  =   self.bot.colour)
        SHOW_EMB.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> Stored Information :",
            value   =   f"```prolog\nGuild ID : {GUILD_ID}\nGuild Name : {ctx.guild.name}\nGuild Owner ID : {OWNER_ID}\n```")
        await ctx.send(embed = SHOW_EMB)

    @data.command(
        name    =   "clear",
        aliases =   ["cl"],
        brief   =   "Delete Information.")
    async def clear_info(self, ctx):
        """Deletes the information stored in database"""
        async def YES(UI : disnake.ui.View, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction, disabled : bool = True):
            if INTERACTION.user != ctx.author:
                await INTERACTION.response.send_message(content = "This is meant for **Guild Administrators** to interact with <a:PAIN:939876989655994488>", ephemeral = True)
            await UI.response.edit(content = f"As you wish, I will be deleting all the information of **{ctx.guild.name}** from my database <:DuckThumbsUp:917007413259956254>", allowed_mentions = self.bot.Mention)
            BUTTON.disabled = True
            await self.bot.DB.execute(f"DELETE FROM guild_info WHERE id = $1", ctx.guild.id)
            await asyncio.sleep(1) 
            await UI.response.edit(content = "Successfully deleted all the information <:Dayum:907110455095480340>", allowed_mentions = self.bot.Mention)
        
        async def NO(UI : disnake.ui.View, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction, disabled : bool = True):
            if INTERACTION.user != ctx.author:
                await INTERACTION.response.send_message(content = "This is meant for **Guild Administrators** to interact with <a:PAIN:939876989655994488>", ephemeral = True)
            await UI.response.edit(content = "Okay <:HaroldSaysOkay:907110916104007681> Seems like you are okay with me storing the information.", allowed_mentions = self.bot.Mention)
            BUTTON.disabled = True
        Confirmation.response = await ctx.reply("Are you sure you want to **delete** all the information stored in the database <:BallManHmm:933398958263386222>", view = Confirmation(YES, NO), allowed_mentions = self.bot.Mention)
    
    @data.command(
        name    =   "add",
        brief   =   "Adds Information")
    async def add_info(self, ctx):
        """Adds data back into the database"""
        async def YES(UI : disnake.ui.View, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction):
            if INTERACTION.user != ctx.author:
                await INTERACTION.response.send_message(content = "This is meant for **Guild Administrators** to interact with <a:PAIN:939876989655994488>", ephemeral = True)
            await UI.response.edit(content = f"As you wish, I will be adding all the information of **{ctx.guild.name}** from my database <:DuckThumbsUp:917007413259956254>", allowed_mentions = self.bot.Mention)
            await self.bot.DB.execute(f"INSERT INTO guild_info (id, name, owner_id) VALUES ($1, $2, $3)", ctx.guild.id, ctx.guild.name, ctx.guild.owner.id)
            await asyncio.sleep(1) 
            await UI.response.edit(content = "Successfully added all the information <:Dayum:907110455095480340>", allowed_mentions = self.bot.Mention)
        
        async def NO(UI : disnake.ui.View, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction, disabled : bool = True):
            if INTERACTION.user != ctx.author:
                await INTERACTION.response.send_message(content = "This is meant for **Guild Administrators** to interact with <a:PAIN:939876989655994488>", ephemeral = True)
            await UI.response.edit(content = f"Okay <:HaroldSaysOkay:907110916104007681> Seems like I'm not adding {ctx.guild.name}'s information today <:SarahThonk:907109849437982750>", allowed_mentions = self.bot.Mention)
            BUTTON.disabled = True
        Confirmation.response = await ctx.reply("Are you sure you want to **add** all the information stored in the database <:BallManHmm:933398958263386222>", view = Confirmation(YES, NO), allowed_mentions = self.bot.Mention)
    
def setup(bot):
    bot.add_cog(Guild(bot))