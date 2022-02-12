import disnake

from disnake.ext import commands

import Source.Kernel.Views.Interface as Interface

class Moderation(commands.Cog):
    """Moderation Commands"""
    def __init__(self, bot):
        self.bot    =   bot

    @staticmethod
    def Check_Hierarchy(ctx, USER : disnake.Member):
        if isinstance(USER, disnake.Member):
            if USER == ctx.bot:
                raise commands.BadArgument(f"They're a bot .__.")
            elif USER == ctx.guild.owner:
                raise commands.BadArgument(f"Oh come on, they're the owner ffs.")
            elif USER == ctx.author:
                raise commands.BadArgument("Self Sabotage, nice... I'm not doing it -")
            elif USER == ctx.guild.me:
               raise commands.BadArgument(f"If you're gonna hurt me - use some other bot.")
            elif USER.top_role > ctx.guild.me.top_role:
                raise commands.BadArgument(f"{USER} has a higher role than me. Raise my powers.")
            return 
        
    @commands.command(
        name    =   "kick",
        brief   =   "Kicks User")
    async def kick(self, ctx, USER : disnake.Member, *, REASON : str = "Not Provided"):
        """Teach them a lesson by kicking them out."""
        self.Check_Hierarchy(ctx, USER)
        async def YES(UI : disnake.ui.View, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction):
            
            await USER.kick(reason = f"{USER} - {REASON} by {ctx.author}")
            KICK_EMB    =   disnake.Embed(
                title   =   f"Kick - Has Occured.",
                description =   f">>> {USER.mention} has been **kicked** <a:Kicked:941667229609631765> !\n<:ReplyContinued:930634770004725821>** - ID :** `{USER.id}`\n<:Reply:930634822865547294>** - On :** {self.bot.DT(ctx.message.created_at, style = 'F')}",
                colour  =   self.bot.colour)
            KICK_EMB.add_field(
                name    =   f"Reason :",
                value   =   f"```prolog\n{REASON}\n```")
            KICK_EMB.timestamp = disnake.utils.utcnow()
            KICK_EMB.set_thumbnail(url = USER.display_avatar.url)
            for View in UI.children:
                View.disabled = True            
            await INTERACTION.response.edit_message(content = f"\u2001", embed = KICK_EMB, view = UI)

            if INTERACTION.user != ctx.author:
                return await INTERACTION.response.send_message(content = f"{Interface.PAIN}", ephemeral = True)
        
        async def NO(UI : disnake.ui.View, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction):
            for View in UI.children:
                View.disabled = True
            await INTERACTION.response.edit_message(content = f"**{USER.mention}** will not be kicked.", allowed_mentions = self.bot.Mention, view = UI)

            if INTERACTION.user != ctx.author:
                return await INTERACTION.response.send_message(content = f"{Interface.PAIN}", ephemeral = True)
    
        Interface.Confirmation.response = await ctx.send(f"Are you sure you want to kick {USER.mention}", view = Interface.Confirmation(YES, NO), allowed_mentions = self.bot.Mention)
    
    @commands.command(
        name    =   "ban",
        brief   =   "Bans User")
    async def ban(self, ctx, USER : disnake.Member, *, REASON : str = "Not Provided"):
        """Ban toxic users"""
        self.Check_Hierarchy(ctx, USER)
        async def YES(UI : disnake.ui.View, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction):
            
            await USER.ban(reason = f"{USER} - {REASON} by {ctx.author}")
            BAN_EMB     =   disnake.Embed(
                title   =   f"Ban Hammer Has Spoken",
                description =   f">>> {USER.mention} has been **banned** <a:Banned:941667204334764042> !\n<:ReplyContinued:930634770004725821>** - ID :** `{USER.id}`\n<:Reply:930634822865547294>** - On :** {self.bot.DT(ctx.message.created_at, style = 'F')}",
                colour  =   self.bot.colour)
            BAN_EMB.add_field(
                name    =   f"Reason :",
                value   =   f"```prolog\n{REASON}\n```")
            BAN_EMB.timestamp = disnake.utils.utcnow()
            BAN_EMB.set_thumbnail(url = USER.display_avatar.url)
            for View in UI.children:
                View.disabled = True            
            await INTERACTION.response.edit_message(content = f"\u2001", embed = BAN_EMB, view = UI)

            if INTERACTION.user != ctx.author:
                return await INTERACTION.response.send_message(content = f"{Interface.PAIN}", ephemeral = True)
        
        async def NO(UI : disnake.ui.View, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction):
            for View in UI.children:
                View.disabled = True
            await INTERACTION.response.edit_message(content = f"**{USER.mention}** will not be banned.", allowed_mentions = self.bot.Mention, view = UI)

            if INTERACTION.user != ctx.author:
                return await INTERACTION.response.send_message(content = f"{Interface.PAIN}", ephemeral = True)
    
        Interface.Confirmation.response = await ctx.send(f"Are you sure you want to ban {USER.mention}", view = Interface.Confirmation(YES, NO), allowed_mentions = self.bot.Mention)
    
def setup(bot):
    bot.add_cog(Moderation(bot))