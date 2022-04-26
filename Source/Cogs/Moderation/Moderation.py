import discord

from discord.ext import commands

import Source.Kernel.Views.Interface as Interface

class Moderation(commands.Cog):
    """Moderation Commands"""
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def Check_Hierarchy(ctx : commands.context, user : discord.Member):
        if isinstance(user, discord.Member):
            if user == ctx.guild.owner:
                raise commands.BadArgument(f"Oh come on, they're the owner ffs.")
            elif not ctx.guild:
                raise commands.BadArgument(f"{ctx.command} can be performed in a guild only")
            elif user == ctx.author:
                raise commands.BadArgument("Self Sabotage, nice... I'm not doing it -")
            elif user == ctx.guild.me:
               raise commands.BadArgument(f"If you're gonna hurt me - use some other bot.")
            elif user.top_role > ctx.guild.me.top_role:
                raise commands.BadArgument(f"{user} has a higher role than me. Raise my powers.")
            return 
        
    @commands.command(
        name = "kick",
        brief = "Kicks User")
    @commands.guild_only()
    @commands.has_guild_permissions(kick_members = True)
    async def kick(self, ctx : commands.context, user : discord.Member, *, reason : str = "Not Provided"):
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{ctx.clean_prefix}{ctx.command}` for the `{ctx.command}` command <:SarahPray:920484222421045258>"
        """Teach them a lesson by kicking them out."""
        self.Check_Hierarchy(ctx, user)
        async def yes(ui : discord.ui.View, interaction : discord.Interaction, button : discord.ui.button):
            if interaction.user != ctx.author:
                await interaction.response.send_message(content = f"{pain}", ephemeral = True)    
            await user.kick(reason = f"{user} - {reason} by {ctx.author}")
            kick_emb = discord.Embed(
                title = "Kick - Has Occured.",
                description = f">>> {user.mention} has been **kicked** <a:Kicked:941667229609631765> !\n<:ReplyContinued:930634770004725821>** - ID :** `{user.id}`\n<:Reply:930634822865547294>** - On :** {self.bot.datetime(ctx.message.created_at, style = 'F')}",
                colour = self.bot.colour)
            kick_emb.add_field(
                name = "Reason :",
                value = f"```prolog\n{reason}\n```")
            kick_emb.timestamp = discord.utils.utcnow()
            kick_emb.set_thumbnail(url = user.display_avatar.url)
            for view in ui.children:
                view.disabled = True            
            await interaction.response.defer()
            await interaction.response.edit_message(content = f"\u2001", embed = kick_emb, view = ui)
        
        async def no(ui : discord.ui.View, interaction : discord.Interaction, button : discord.ui.button):
            if interaction.user != ctx.author:
                await interaction.response.send_message(content = f"{pain}", ephemeral = True)    
            for view in ui.children:
                view.disabled = True
            await interaction.response.edit_message(content = f"**{user.mention}** will not be kicked.", allowed_mentions = self.bot.mentions, view = ui)
    
        Interface.Confirmation.response = await ctx.send(f"Are you sure you want to kick {user.mention}", view = Interface.Confirmation(yes, no), allowed_mentions = self.bot.mentions)

    @commands.command(
        name = "ban",
        brief = "Bans User")
    @commands.guild_only()
    @commands.has_guild_permissions(ban_members = True)
    async def kick(self, ctx : commands.context, user : discord.Member, *, reason : str = "Not Provided"):
        """Teach them a lesson by kicking them out."""
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{ctx.clean_prefix}{ctx.command}` for the `{ctx.command}` command <:SarahPray:920484222421045258>"
        self.Check_Hierarchy(ctx, user)
        async def yes(ui : discord.ui.View, interaction : discord.Interaction, button : discord.ui.button):
            if interaction.user != ctx.author:
                await interaction.response.send_message(content = f"{pain}", ephemeral = True)    
            await user.kick(reason = f"{user} - {reason} by {ctx.author}")
            ban_emb = discord.Embed(
                title = "Kick - Has Occured.",
                description = f">>> {user.mention} has been **banned** <a:Banned:941667204334764042> !\n<:ReplyContinued:930634770004725821>** - ID :** `{user.id}`\n<:Reply:930634822865547294>** - On :** {self.bot.datetime(ctx.message.created_at, style = 'F')}",
                colour = self.bot.colour)
            ban_emb.add_field(
                name = "Reason :",
                value = f"```prolog\n{reason}\n```")
            ban_emb.timestamp = discord.utils.utcnow()
            ban_emb.set_thumbnail(url = user.display_avatar.url)
            for view in ui.children:
                view.disabled = True            
            await interaction.response.edit_message(content = f"\u2001", embed = ban_emb, view = ui)
        
        async def no(ui : discord.ui.View, interaction : discord.Interaction, button : discord.ui.button):
            if interaction.user != ctx.author:
                await interaction.response.send_message(content = f"{pain}", ephemeral = True)
            for view in ui.children:
                view.disabled = True
            await interaction.response.edit_message(content = f"**{user.mention}** will not be banned.", allowed_mentions = self.bot.mentions, view = ui)
    
        Interface.Confirmation.response = await ctx.send(f"Are you sure you want to ban {user.mention}", view = Interface.Confirmation(yes, no), allowed_mentions = self.bot.mentions)
  
    @commands.command(
        name = "mute",
        brief = "Mutes User")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles = True)
    async def mute(self, ctx : commands.context, user : discord.Member, *, reason : str = "Not Provided"):
        """Mute toxic users"""
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{ctx.clean_prefix}{ctx.command}` for the `{ctx.command}` command <:SarahPray:920484222421045258>"
        self.Check_Hierarchy(ctx, user)
        role = discord.utils.get(ctx.guild.roles, name = "Muted")
        if role in user.roles:
                await ctx.send(f"**{user}** already has the role and is currently muted <a:LifeSucks:932255208044650596>")                
        else:        
            async def yes(ui : discord.ui.View, interaction : discord.Interaction, button : discord.ui.button):
                if interaction.user != ctx.author:
                    await interaction.response.send_message(content = f"{pain}", ephemeral = True)  
                if not role:
                    create_role = await ctx.guild.create_role(name = "Muted", permissions = discord.Permissions(66560), reason = "Mute command needs Muted role", colour = discord.Colour.from_rgb(255, 100, 100))
                    for channel in ctx.guild.channels:
                        await channel.set_permissions(role, send_messages = False, read_messages = True, view_channel = False)
            
                for view in ui.children:
                    view.disabled = True            
    
                try:
                    await user.add_roles(role, reason = reason)
                except Exception as exception:
                    await ctx.send(exception)

                mute_emb = discord.Embed(
                    title = f"<:CustomScroll2:933390953471955004> Mute Has Occured",
                    description = f">>> {user.mention} has been **muted** <a:Mute:941667157278871612>!\n<:ReplyContinued:930634770004725821>** - ID :** `{user.id}`\n<:Reply:930634822865547294>** - On :** {self.bot.datetime(ctx.message.created_at, style = 'F')}",
                    colour = self.bot.colour)
                mute_emb.add_field(
                    name = "Reason :",
                    value = f"```prolog\n{reason}\n```")
                mute_emb.timestamp = discord.utils.utcnow()
                mute_emb.set_thumbnail(url = user.display_avatar.url)
                await user.send(embed = mute_emb)
                await interaction.response.edit_message(content = f"\u2001", embed = mute_emb, view = ui)

            async def no(ui : discord.ui.View, interaction : discord.Interaction, button : discord.ui.button):
                if interaction.user != ctx.author:
                    await interaction.response.send_message(content = f"{pain}", ephemeral = True)
                for view in ui.children:
                    view.disabled = True
                await interaction.response.edit_message(content = f"**{user.mention}** will not be muted.", allowed_mentions = self.bot.mentions, view = ui)

        Interface.Confirmation.response = await ctx.send(f"Are you sure you want to **mute** {user.mention}\n<:Reply:930634822865547294> **- For :** {reason}", view = Interface.Confirmation(ctx, yes, no), allowed_mentions = self.bot.Mention)

    @commands.command(
        name = "unmute",
        brief = "Unmutes User")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles = True)
    async def unmute(self, ctx : commands.context, user : discord.Member, *, reason : str = "Not Provided"):
        """Unmute users"""
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{ctx.clean_prefix}{ctx.command}` for the `{ctx.command}` command <:SarahPray:920484222421045258>"
        self.Check_Hierarchy(ctx, user)
        role = discord.utils.get(ctx.guild.roles, name = "Muted")
        async def yes(ui : discord.ui.View, interaction : discord.Interaction, button : discord.ui.button):
            if interaction.user != ctx.author:
                await interaction.response.send_message(content = f"{pain}", ephemeral = True)
            if not role:
                create_role = await ctx.guild.create_role(name = "Muted", permissions = discord.Permissions(66560), reason = "Mute command needs Muted role", colour = discord.Colour.from_rgb(255, 100, 100))
                for channel in ctx.guild.channels:
                    await channel.set_permissions(role, send_messages = False, read_messages = True, view_channel = False)
            
            for view in ui.children:
                view.disabled = True            
    
            try:
                await user.remove_roles(role, reason = reason)
            except Exception as exception:
                await ctx.send(exception)

            unmute_emb = discord.Embed(
                title = f"<:CustomScroll2:933390953471955004> Unmute Has Occured",
                description = f">>> {user.mention} has been **unmuted** <a:Mute:941667157278871612>!\n<:ReplyContinued:930634770004725821>** - ID :** `{user.id}`\n<:Reply:930634822865547294>** - On :** {self.bot.datetime(ctx.message.created_at, style = 'F')}",
                colour = self.bot.colour)
            unmute_emb.add_field(
                name = f"Reason :",
                value = f"```prolog\n{reason}\n```")
            unmute_emb.timestamp = discord.utils.utcnow()
            unmute_emb.set_thumbnail(url = user.display_avatar.url)
            await user.send(embed = unmute_emb)
            await interaction.response.edit_message(content = f"\u2001", embed = unmute_emb, view = ui)

        async def no(ui : discord.ui.View, interaction : discord.Interaction, button : discord.ui.button):
            if interaction.user != ctx.author:
                await interaction.response.send_message(content = f"{pain}", ephemeral = True)
            for view in ui.children:
                view.disabled = True
            await interaction.response.edit_message(content = f"**{user.mention}** will not be unmuted.", allowed_mentions = self.bot.mentions, view = ui)

        Interface.Confirmation.response = await ctx.send(f"Are you sure you want to **unmute** {user.mention}\n<:Reply:930634822865547294> **- For :** {reason}", view = Interface.Confirmation(ctx, yes, no), allowed_mentions = self.bot.mentions)

    @commands.command(
        name = "setnick",
        brief = "Change Nick",
        aliases = ["nick"])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_nicknames = True)
    async def nick(self, ctx : commands.context, user : discord.Member, *, nick : str):
        """Change the Nickname of a member"""
        self.Check_Hierarchy(ctx, user)
        
        previous_nickname = user.display_name
        await user.edit(nick = nick)
        new_nickname = nick

        nick_emb = discord.Embed(
            title = f"<:CustomScroll1:933391442427138048> {user}'s Nick Changed!",
            description = f">>> <:GeraltRightArrow:904740634982760459> {ctx.message.author.mention} has changed {user.mention} nickname :\n\n" \
                          f" <:ReplyContinued:930634770004725821> **- From :** `{previous_nickname}`\n" \
                          f" <:Reply:930634822865547294> **- To :** `{new_nickname}`",
            colour = self.bot.colour)
        nick_emb.set_thumbnail(url = user.display_avatar.url)
        nick_emb.timestamp = discord.utils.utcnow()
        await ctx.reply(f"<:GeraltRightArrow:904740634982760459> {user.mention}'s nickname has been `changed` -\n>>> <:ReplyContinued:930634770004725821> - From : {previous_nickname}\n<:Reply:930634822865547294> - To : {new_nickname} \n**Event Occured On :** {self.bot.datetime(discord.utils.utcnow(), style = 'F')} <a:IEat:940413722537644033>", allowed_mentions = self.bot.mentions)

async def setup(bot):
    await bot.add_cog(Moderation(bot))