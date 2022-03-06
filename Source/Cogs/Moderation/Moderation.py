import discord

from discord.ext import commands

import Source.Kernel.Views.Interface as Interface

class Moderation(commands.Cog):
    """Moderation Commands"""
    def __init__(self, bot):
        self.bot    =   bot

    @staticmethod
    def Check_Hierarchy(ctx, USER : discord.Member):
        if isinstance(USER, discord.Member):
            if USER == ctx.guild.owner:
                raise commands.BadArgument(f"Oh come on, they're the owner ffs.")
            elif not ctx.guild:
                raise commands.BadArgument(f"{ctx.command} can be performed in a guild only")
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
    @commands.has_guild_permissions(kick_members = True)
    async def kick(self, ctx, USER : discord.Member, *, REASON : str = "Not Provided"):
        """Teach them a lesson by kicking them out."""
        self.Check_Hierarchy(ctx, USER)
        async def YES(UI : discord.ui.View, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
            
            await USER.kick(reason = f"{USER} - {REASON} by {ctx.author}")
            KICK_EMB    =   discord.Embed(
                title   =   f"Kick - Has Occured.",
                description =   f">>> {USER.mention} has been **kicked** <a:Kicked:941667229609631765> !\n<:ReplyContinued:930634770004725821>** - ID :** `{USER.id}`\n<:Reply:930634822865547294>** - On :** {self.bot.DT(ctx.message.created_at, style = 'F')}",
                colour  =   self.bot.colour)
            KICK_EMB.add_field(
                name    =   f"Reason :",
                value   =   f"```prolog\n{REASON}\n```")
            KICK_EMB.timestamp = discord.utils.utcnow()
            KICK_EMB.set_thumbnail(url = USER.display_avatar.url)
            for View in UI.children:
                View.disabled = True            
            await INTERACTION.response.edit_message(content = f"\u2001", embed = KICK_EMB, view = UI)

            if INTERACTION.user != ctx.author:
                return await INTERACTION.response.send_message(content = f"{Interface.PAIN}", ephemeral = True)
        
        async def NO(UI : discord.ui.View, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
            for View in UI.children:
                View.disabled = True
            await INTERACTION.response.edit_message(content = f"**{USER.mention}** will not be kicked.", allowed_mentions = self.bot.Mention, view = UI)

            if INTERACTION.user != ctx.author:
                return await INTERACTION.response.send_message(content = f"{Interface.PAIN}", ephemeral = True)
    
        Interface.Confirmation.response = await ctx.send(f"Are you sure you want to kick {USER.mention}", view = Interface.Confirmation(YES, NO), allowed_mentions = self.bot.Mention)
    
    @commands.command(
        name    =   "ban",
        brief   =   "Bans User")
    @commands.has_guild_permissions(ban_members = True)
    async def ban(self, ctx, USER : discord.Member, *, REASON : str = "Not Provided"):
        """Ban toxic users"""
        self.Check_Hierarchy(ctx, USER)
        async def YES(UI : discord.ui.View, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
            
            await USER.ban(reason = f"{USER} - {REASON} by {ctx.author}")
            BAN_EMB     =   discord.Embed(
                title   =   f"<:CustomScroll1:933391442427138048> Ban Hammer Has Spoken",
                description =   f">>> {USER.mention} has been **banned** <a:Banned:941667204334764042> !\n<:ReplyContinued:930634770004725821>** - ID :** `{USER.id}`\n<:Reply:930634822865547294>** - On :** {self.bot.DT(ctx.message.created_at, style = 'F')}",
                colour  =   self.bot.colour)
            BAN_EMB.add_field(
                name    =   f"Reason :",
                value   =   f"```prolog\n{REASON}\n```")
            BAN_EMB.timestamp = discord.utils.utcnow()
            BAN_EMB.set_thumbnail(url = USER.display_avatar.url)
            for View in UI.children:
                View.disabled = True            
            await INTERACTION.response.edit_message(content = f"\u2001", embed = BAN_EMB, view = UI)

            if INTERACTION.user != ctx.author:
                return await INTERACTION.response.send_message(content = f"{Interface.PAIN}", ephemeral = True)
        
        async def NO(UI : discord.ui.View, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
            for View in UI.children:
                View.disabled = True
            await INTERACTION.response.edit_message(content = f"**{USER.mention}** will not be banned.", allowed_mentions = self.bot.Mention, view = UI)

            if INTERACTION.user != ctx.author:
                return await INTERACTION.response.send_message(content = f"{Interface.PAIN}", ephemeral = True)
    
        Interface.Confirmation.response = await ctx.send(f"Are you sure you want to ban {USER.mention}", view = Interface.Confirmation(YES, NO), allowed_mentions = self.bot.Mention)
    
    @commands.command(
        name    =   "mute",
        brief   =   "Mutes User")
    @commands.has_guild_permissions(manage_roles = True)
    async def mute(self, ctx, USER : discord.Member, *, REASON : str = "Not Provided"):
        """Mute toxic users"""
        self.Check_Hierarchy(ctx, USER)
        ROLE    =   discord.utils.get(ctx.guild.roles, name = "Muted")
        if ROLE in USER.roles:
                await ctx.send(f"**{USER}** already has the role and is currently muted <a:LifeSucks:932255208044650596>")                
        else:        
            async def YES(UI : discord.ui.View, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
                if not ROLE:
                    CREATE_ROLE = await ctx.guild.create_role(name = "Muted", permissions = discord.Permissions(66560), reason = "Mute command needs Muted role", colour = discord.Colour.from_rgb(255, 100, 100))
                    for channel in ctx.guild.channels:
                        await channel.set_permissions(ROLE, send_messages = False, read_messages = True, view_channel = False)
            
                for View in UI.children:
                    View.disabled = True            
    
                try:
                    await USER.add_roles(ROLE, reason = REASON)
                except Exception as e:
                    await ctx.send(e)

                MUTE_EMB     =   discord.Embed(
                    title   =   f"<:CustomScroll2:933390953471955004> Mute Has Occured",
                    description =   f">>> {USER.mention} has been **muted** <a:Mute:941667157278871612>!\n<:ReplyContinued:930634770004725821>** - ID :** `{USER.id}`\n<:Reply:930634822865547294>** - On :** {self.bot.DT(ctx.message.created_at, style = 'F')}",
                    colour  =   self.bot.colour)
                MUTE_EMB.add_field(
                    name    =   f"Reason :",
                    value   =   f"```prolog\n{REASON}\n```")
                MUTE_EMB.timestamp = discord.utils.utcnow()
                MUTE_EMB.set_thumbnail(url = USER.display_avatar.url)
                await INTERACTION.response.edit_message(content = f"\u2001", embed = MUTE_EMB, view = UI)

                if INTERACTION.user != ctx.author:
                    return await INTERACTION.response.send_message(content = f"{Interface.PAIN}", ephemeral = True)

            async def NO(UI : discord.ui.View, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
                for View in UI.children:
                    View.disabled = True
                await INTERACTION.response.edit_message(content = f"**{USER.mention}** will not be muted.", allowed_mentions = self.bot.Mention, view = UI)

                if INTERACTION.user != ctx.author:
                    return await INTERACTION.response.send_message(content = f"{Interface.PAIN}", ephemeral = True)

            Interface.Confirmation.response = await ctx.send(f"Are you sure you want to **mute** {USER.mention}\n<:Reply:930634822865547294> **- For :** {REASON}", view = Interface.Confirmation(YES, NO), allowed_mentions = self.bot.Mention)

    @commands.command(
        name    =   "unmute",
        brief   =   "Unmutes User")
    @commands.has_guild_permissions(manage_roles = True)
    async def unmute(self, ctx, USER : discord.Member, *, REASON : str = "Not Provided"):
        """Unmute users"""
        self.Check_Hierarchy(ctx, USER)
        ROLE    =   discord.utils.get(ctx.guild.roles, name = "Muted")
        async def YES(UI : discord.ui.View, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
            if not ROLE:
                CREATE_ROLE = await ctx.guild.create_role(name = "Muted", permissions = discord.Permissions(66560), reason = "Mute command needs Muted role", colour = discord.Colour.from_rgb(255, 100, 100))
                for channel in ctx.guild.channels:
                    await channel.set_permissions(ROLE, send_messages = False, read_messages = True, view_channel = False)
            
            for View in UI.children:
                View.disabled = True            
    
            try:
                await USER.remove_roles(ROLE, reason = REASON)
            except Exception as e:
                await ctx.send(e)

            UNMUTE_EMB     =   discord.Embed(
                title   =   f"<:CustomScroll2:933390953471955004> Unmute Has Occured",
                description =   f">>> {USER.mention} has been **unmuted** <a:Mute:941667157278871612>!\n<:ReplyContinued:930634770004725821>** - ID :** `{USER.id}`\n<:Reply:930634822865547294>** - On :** {self.bot.DT(ctx.message.created_at, style = 'F')}",
                colour  =   self.bot.colour)
            UNMUTE_EMB.add_field(
                name    =   f"Reason :",
                value   =   f"```prolog\n{REASON}\n```")
            UNMUTE_EMB.timestamp = discord.utils.utcnow()
            UNMUTE_EMB.set_thumbnail(url = USER.display_avatar.url)
            await INTERACTION.response.edit_message(content = f"\u2001", embed = UNMUTE_EMB, view = UI)

            if INTERACTION.user != ctx.author:
                return await INTERACTION.response.send_message(content = f"{Interface.PAIN}", ephemeral = True)

        async def NO(UI : discord.ui.View, BUTTON : discord.ui.button, INTERACTION : discord.Interaction):
            for View in UI.children:
                View.disabled = True
            await INTERACTION.response.edit_message(content = f"**{USER.mention}** will not be unmuted.", allowed_mentions = self.bot.Mention, view = UI)

            if INTERACTION.user != ctx.author:
                return await INTERACTION.response.send_message(content = f"{Interface.PAIN}", ephemeral = True)

        Interface.Confirmation.response = await ctx.send(f"Are you sure you want to **unmute** {USER.mention}\n<:Reply:930634822865547294> **- For :** {REASON}", view = Interface.Confirmation(YES, NO), allowed_mentions = self.bot.Mention)
    
    @commands.command(
        name    =   "setnick",
        aliases =   ["nick"],
        brief   =   "Change Nick")
    @commands.has_guild_permissions(manage_nicknames = True)
    async def nick(self, ctx, USER : discord.Member, *, NICK : str):
        """Change the Nickname of a member"""
        self.Check_Hierarchy(ctx, USER)
        Previous_Nickname   =   USER.display_name
        await USER.edit(nick = NICK)
        New_Nickname        =   NICK

        NICK_EMB    =   discord.Embed(
            title   =   f"<:CustomScroll1:933391442427138048> {USER}'s Nick Changed!",
            description =   f">>> <:GeraltRightArrow:904740634982760459> {ctx.message.author.mention} has changed {USER.mention} nickname :\n\n" \
                            f" <:ReplyContinued:930634770004725821> **- From :** `{Previous_Nickname}`\n" \
                            f" <:Reply:930634822865547294> **- To :** `{New_Nickname}`",
            colour  =   self.bot.colour)
        NICK_EMB.set_thumbnail(url = USER.display_avatar.url)
        NICK_EMB.timestamp  =   discord.utils.utcnow()
        await ctx.reply(f"<:GeraltRightArrow:904740634982760459> {USER.mention}'s nickname has been `changed` -\n>>> <:ReplyContinued:930634770004725821> - From : {Previous_Nickname}\n<:Reply:930634822865547294> - To : {New_Nickname} \n**Event Occured On :** {self.bot.DT(discord.utils.utcnow(), style = 'F')} <a:IEat:940413722537644033>", allowed_mentions = self.bot.Mention)

def setup(bot):
    bot.add_cog(Moderation(bot))