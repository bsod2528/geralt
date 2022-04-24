import typing
import discord
import humanize

from discord.ext import commands
from discord.enums import ButtonStyle

import Source.Kernel.Utilities.Flags as Flags
import Source.Kernel.Views.Interface as Interface
import Source.Kernel.Views.Paginator as Paginator

class Utility(commands.Cog):
    """Utility Commands"""
    def __init__(self, bot):
        self.bot = bot

    # Get user's PFP
    @commands.command(
        name = "avatar",
        brief = "View a persons PFP",
        aliases = ["pfp", "pp", "dp", "av"])
    async def avatar(self, ctx : commands.context, *, user : discord.Member = None):
        """See the user's PFP in an enlarged manner"""
        user = user or ctx.author
        await Interface.PFP(self.bot, ctx, user).send(ctx)

    # Get user's information
    @commands.command(
        name = "userinfo",
        brief = "Get user information",
        aliases = ["user", "ui"])
    async def userinfo(self, ctx : commands.context, *, user : discord.Member = None):
        """Get entire details about a user."""
        user = user or ctx.author
        roles = ""
        for role in user.roles:
            if role is ctx.guild.default_role: continue
            roles = f"{roles} {role.mention}"
        if roles != "":
            roles = f"{roles}"
        fetched_user = await ctx.bot.fetch_user(user.id)
        permissions = Flags.user_perms(user.guild_permissions)
        if permissions:
            perms_ = f"{' **|** '}".join(permissions)
        avatar = user.display_avatar.with_static_format("png")
        activity = discord.utils.find(lambda act: isinstance(act, discord.CustomActivity), user.activities)
        activity_holder = f"`{discord.utils.remove_markdown(activity.name)}`" if activity and activity.name else f'`{user}` has no activity at the moment.'

        general_emb = discord.Embed(
            title = f":scroll: {user}'s Information",
            colour = user.colour)
        general_emb.add_field(
            name = "<:GeraltRightArrow:904740634982760459> General Info :",
            value = f"> **<:ReplyContinued:930634770004725821> - Name :** {user.mention} \n" \
                    f"> **<:ReplyContinued:930634770004725821> - Nickname :** {(user.nick) or 'No nickname set'} \n" \
                    f"> **<:ReplyContinued:930634770004725821> - Discriminator :** `#{user.discriminator}` \n"
                    f"> **<:Reply:930634822865547294> - Identification No. :** `{user.id}` \n")
        general_emb.add_field(
            name = "<:GeraltRightArrow:904740634982760459> Account Info :",
            value = f"> **<:ReplyContinued:930634770004725821> - Created on :**{self.bot.datetime(user.created_at, style = 'D')} ({self.bot.datetime(user.created_at, style = 'R')}) \n" \
                    f"> **<:Reply:930634822865547294> - Joined Guild on :**{self.bot.datetime(user.joined_at, style = 'D')} ({self.bot.datetime(user.joined_at, style = 'R')})\n",
            inline = False)
        general_emb.set_thumbnail(url = avatar)
        general_emb.timestamp = discord.utils.utcnow()

        guild_emb = discord.Embed(
            title = f":scroll: {user} in {ctx.guild}",
            colour = user.colour)
        guild_emb.add_field(
            name = "<:GeraltRightArrow:904740634982760459> Permissions Present :",
            value = f"> **<:Reply:930634822865547294> -** {perms_}")
        guild_emb.add_field(
            name = "<:GeraltRightArrow:904740634982760459> Top Most Role :",
            value = f"> **<:Reply:930634822865547294> -** {user.top_role.mention}",
            inline = False)
        guild_emb.add_field(
            name = "<:GeraltRightArrow:904740634982760459> All Roles Present :",
            value = f"> **<:Reply:930634822865547294> -** {roles}",
            inline = False)
        guild_emb.set_thumbnail(url = avatar)
        guild_emb.timestamp = discord.utils.utcnow()

        misc_emb = discord.Embed(
            title = f":scroll: {user}'s - Misc. Information",
            colour = user.colour)
        misc_emb.add_field(
            name = "<:GeraltRightArrow:904740634982760459> Badges Present :",
            value = f"> **<:Reply:930634822865547294> - **{Flags.user_badges(user = user, fetch_user = fetched_user) if Flags.user_badges(user = user, fetch_user = fetched_user) else '`No Badges Present`'}")
        misc_emb.add_field(
            name = "<:GeraltRightArrow:904740634982760459> Accent Colours :",
            value = f"> **<:ReplyContinued:930634770004725821> - Banner Colour :** `{str(fetched_user.accent_colour).upper()}` \n" \
                    f"> **<:Reply:930634822865547294> - Guild Role Colour :** `{user.color if user.color is not discord.Color.default() else 'Default'}`",
            inline = False)  
        misc_emb.add_field(
            name = "Activity :",
            value = f"> **<:Reply:930634822865547294> -** {activity_holder}",
            inline = False)
        misc_emb.set_thumbnail(url = avatar)
        misc_emb.timestamp = discord.utils.utcnow()
        
        pfp_emb = discord.Embed(
            title = f":scroll: {user}'s PFP",
            description = f"[**JPG Format**]({user.display_avatar.with_static_format('jpg')}) **|** [**PNG Format**]({user.display_avatar.with_static_format('png')}) **|** [**WEBP Format**]({user.display_avatar.with_static_format('webp')})",
            colour = user.colour)
        pfp_emb.set_image(url = avatar)
        pfp_emb.timestamp = discord.utils.utcnow()

        banner_emb = None

        if fetched_user.banner is None:
            embed_list = [general_emb, guild_emb, misc_emb, pfp_emb]
            await ctx.trigger_typing()
            await Paginator.Paginator(self.bot, ctx, embeds = embed_list).send(ctx)
        else:
            banner_emb = discord.Embed(
                title = f":scroll: {user}'s Banner",
                description = f"[**Download Banner Here**]({fetched_user.banner.url})",
                colour = user.colour)
            banner_emb.set_image(url = fetched_user.banner.url)
            banner_emb.timestamp = discord.utils.utcnow()
            
            embed_list = [general_emb, guild_emb, misc_emb, pfp_emb, banner_emb]
            await ctx.trigger_typing()
            await Paginator.Paginator(self.bot, ctx, embeds = embed_list).send(ctx) 

    @commands.command(
        name = "serverinfo",
        brief = "Get guild information",
        aliases = ["si", "gi"])
    @commands.guild_only()
    async def server_info(self, ctx : commands.context):
        """Get entire details about the guild."""
        user_status = [
                        len(list(filter(lambda u : str(u.status) == "online", ctx.guild.members))),
                        len(list(filter(lambda u : str(u.status) == "idle", ctx.guild.members))),
                        len(list(filter(lambda u : str(u.status) == "dnd", ctx.guild.members))),
                        len(list(filter(lambda u : str(u.status) == "offline", ctx.guild.members)))
                      ]
        fetched_guild = await ctx.bot.fetch_guild(ctx.guild.id)

        general_emb = discord.Embed(
            title = f":scroll: {ctx.guild.name}'s Information",
            colour = self.bot.colour)
        general_emb.add_field(
            name = "<:GeraltRightArrow:904740634982760459> General Information :",
            value = f"> **<:ReplyContinued:930634770004725821> - <a:Owner:905750348457738291> Owner :** {ctx.guild.owner.mention} (`{ctx.guild.owner.id}`) \n" \
                    f"> **<:ReplyContinued:930634770004725821> - <a:Users:905749451350638652> No. of Roles :** `{len(ctx.guild.roles)}` \n" \
                    f"> **<:ReplyContinued:930634770004725821> - <a:Info:905750331789561856> Identification No. :** `{ctx.guild.id}` \n" \
                    f"> **<:ReplyContinued:930634770004725821> - <a:Verify:905748402871095336> Verification Level :** {str(ctx.guild.verification_level).replace('_', ' ').replace('`NONE`', '`NILL`').title()} \n" \
                    f"> **<:Reply:930634822865547294> - <:WinFileBruh:898571301986373692> File Transfer Limit:** `{humanize.naturalsize(ctx.guild.filesize_limit)}`")
        general_emb.add_field(
            name = "<:GeraltRightArrow:904740634982760459> Initialisation :",
            value = f"> **<:ReplyContinued:930634770004725821> - <a:Woo:905754435379163176> Made On :** {self.bot.datetime(ctx.guild.created_at)} \n" \
                    f"> **<:Reply:930634822865547294> - <:ISus:915817563307515924> Media Filteration :** For `{str(ctx.guild.explicit_content_filter).replace('_',' ').replace('`NONE`', '`NILL`').title()}` \n",
            inline = False)
        general_emb.set_thumbnail(url = ctx.guild.icon.url)
        general_emb.timestamp = discord.utils.utcnow()

        other_emb = discord.Embed(
            title = f":scroll: {ctx.guild.name}'s Other Information",
            colour = self.bot.colour)
        other_emb.add_field(
            name ="<:GeraltRightArrow:904740634982760459> Channel Information :",
            value = f"> **<:ReplyContinued:930634770004725821> - <:Channel:905674680436944906> Text :** `{len(ctx.guild.text_channels)}` \n" \
                    f"> **<:ReplyContinued:930634770004725821> - <:Voice:905746719034187796> Voice :** `{len(ctx.guild.voice_channels)}` \n" \
                    f"> **<:ReplyContinued:930634770004725821> - <a:Thread:905750997706629130> Threads :** `{len(ctx.guild.threads)}` \n" \
                    f"> **<:Reply:930634822865547294> - <:StageChannel:905674422839554108> Stage :** `{len(ctx.guild.stage_channels)}` \n",
            inline = False)
        other_emb.add_field(
            name = "<:GeraltRightArrow:904740634982760459> Emotes Present :",
            value = f"> **<:ReplyContinued:930634770004725821> - <a:IThink:933315875501641739> Animated :** `{len([animated for animated in ctx.guild.emojis if animated.animated])}` / `{ctx.guild.emoji_limit}` \n" \
                    f"> **<:Reply:930634822865547294> - <:BallManHmm:933398958263386222> Non - Animated :** `{len([non_animated for non_animated in ctx.guild.emojis if not non_animated.animated])}` / `{ctx.guild.emoji_limit}`",
            inline = False)
        other_emb.set_thumbnail(url = ctx.guild.icon.url)
        other_emb.timestamp = discord.utils.utcnow()

        user_emb = discord.Embed(
            title = f":scroll: {ctx.guild.name}'s Users Information",
            colour = self.bot.colour)
        user_emb.add_field(
            name = "<:GeraltRightArrow:904740634982760459> No. of User :",
            value = f"> **<:ReplyContinued:930634770004725821> - <a:HumanBro:905748764432662549> No. of Humans :** `{len(list(filter(lambda u : u.bot is False, ctx.guild.members)))}` \n" \
                    f"> **<:ReplyContinued:930634770004725821> - <a:BotLurk:905749164355379241> No. of Bots :** `{len(list(filter(lambda u : u.bot, ctx.guild.members)))}` \n" \
                    f"> **<:Reply:930634822865547294> - <a:Users:905749451350638652> Total :** `{ctx.guild.member_count}` \n",
            inline  =   False)
        user_emb.add_field(
            name = "<:GeraltRightArrow:904740634982760459> Activity Information :",
            value = f"> **<:ReplyContinued:930634770004725821> - <:Online:905757053119766528> Online :** `{user_status[0]}` \n" \
                    f"> **<:ReplyContinued:930634770004725821> - <:Idle:905757063064453130> Idle :** `{user_status[1]}` \n" \
                    f"> **<:ReplyContinued:930634770004725821> - <:DnD:905759353141874709> Do Not Disturb :** `{user_status[2]}` \n" \
                    f"> **<:Reply:930634822865547294> - <:Offline:905757032521551892> Offline :** `{user_status[3]}`",
            inline = False)
        user_emb.set_thumbnail(url = ctx.guild.icon.url)
        user_emb.timestamp = discord.utils.utcnow()
    
        icon_emb = discord.Embed(
            title = f":scroll: {ctx.guild.name}'s Icon",
            description = f"[**JPG Format**]({ctx.guild.icon.with_static_format('jpg')}) **|** [**PNG Format**]({ctx.guild.icon.with_static_format('png')}) **|** [**WEBP Format**]({ctx.guild.icon.with_static_format ('webp')})",
            colour = self.bot.colour)
        icon_emb.set_image(url = ctx.guild.icon.url)
        icon_emb.timestamp = discord.utils.utcnow()

        banner_emb = None

        if fetched_guild.banner is None:
            embed_list = [general_emb, other_emb, user_emb, icon_emb]
            await ctx.trigger_typing()
            await Paginator.Paginator(self.bot, ctx, embeds = embed_list).send(ctx)
        else:
            banner_emb = discord.Embed(
                title = f":scroll: {ctx.guild.name}'s Banner",
                description = f"[**Download Banner Here**]({fetched_guild.banner.url})",
                colour = self.bot.colour)
            banner_emb.set_image(url = fetched_guild.banner.url)
            banner_emb.timestamp = discord.utils.utcnow()
            
            embed_list = [general_emb, other_emb, user_emb, icon_emb, banner_emb]
            await ctx.trigger_typing()
            await Paginator.Paginator(self.bot, ctx, embeds = embed_list).send(ctx)

    @commands.group(
        name = "todo",
        brief = "List User's Todo List.",
        aliases = ["td"])
    async def todo(self, ctx : commands.context):
        """Sends Todo sub - commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @todo.command(
        name = "add",
        brief = "Add item to your list.")
    async def todo_add(self, ctx : commands.context, *, task : str = None):
        """Add tasks to your todo list."""
        await self.bot.db.execute(f"INSERT INTO todo (user_name, user_id, discriminator, task, task_created_at, url) VALUES ($1, $2, $3, $4, $5, $6) RETURNING task_id", ctx.author.name, ctx.author.id, ctx.author.discriminator, task, ctx.message.created_at, ctx.message.jump_url)
        task_id = await self.bot.db.fetchval(f"SELECT task_id FROM todo WHERE task = $1", task)
        await ctx.reply(f"Successfully added task.\n<:Reply:930634822865547294> **Task ID -** `{task_id}`")

    @todo.command(
        name = "list",
        brief = "See your todo list.",
        aliases = ["show"])  
    async def todo_list(self, ctx : commands.context):
        """See your entire todo list."""
        fetch_tasks = await self.bot.db.fetch(f"SELECT * FROM todo WHERE user_id = $1", ctx.author.id)
        task_list = []
        serial_no = 1
        for tasks in fetch_tasks:
            task_list.append(f"> [**{serial_no})**]({tasks['url']}) \"**{tasks['task']}**\"\n> │ ` ─ ` ID : {tasks['task_id']}\n> │ ` ─ ` Created : {self.bot.datetime(tasks['task_created_at'], style = 'R')}\n────\n")
            serial_no += 1
        
        if not fetch_tasks:
            await ctx.reply(f"You currently have `0` tasks present. To start listing out tasks, run `{ctx.clean_prefix}todo add <TASK>` <a:LifeSucks:932255208044650596>")
        else:
            if serial_no <= 3:
                todo_list_emb = discord.Embed(
                    title = f":scroll: {ctx.author}'s Todo List :",
                    description = f"".join(tasks for tasks in task_list),
                    colour = self.bot.colour)
                todo_list_emb.set_thumbnail(url = ctx.author.display_avatar.url)
                todo_list_emb.set_footer(text = f"Run {ctx.clean_prefix}todo for more sub - commands.")
                todo_list_emb.timestamp = discord.utils.utcnow()
                await ctx.reply(embed = todo_list_emb, mention_author = False)
            else:
                # Huge thanks to Zeus432 [ Github ID ] for helping me enable the pagination :D
                embed_list = []
                while task_list:
                    todo_list_embs = discord.Embed(
                        title = f":scroll: {ctx.author}'s Todo List :",
                        description = "".join(task_list[:3]),
                        colour = self.bot.colour)
                    todo_list_embs.set_thumbnail(url = ctx.author.display_avatar.url)
                    todo_list_embs.set_footer(text = f"Run {ctx.clean_prefix}todo for more sub - commands.")
                    todo_list_embs.timestamp = discord.utils.utcnow()
                    task_list = task_list[3:]
                    embed_list.append(todo_list_embs)     
                await Paginator.Paginator(self.bot, ctx, embeds = embed_list).send(ctx) 

    @todo.command(
        name = "edit",
        brief = "Edit task")    
    async def todo_edit(self, ctx : commands.context, id : int, *, edited : str):
        """Edit a particular task."""
        
        if id != await self.bot.db.fetchval(f"SELECT * FROM todo WHERE task_id = $1 AND user_name = $2", id, ctx.author.name):
            await ctx.reply(f"<:GeraltRightArrow:904740634982760459> **Task ID -** `{id}` - is a task either which you do not own or is not present in the database <:DutchySMH:930620665139191839>")
        else:
            await self.bot.db.execute(f"UPDATE todo SET task = $1, url = $2, task_created_at = $3 WHERE task_id = $4", edited, ctx.message.jump_url, ctx.message.created_at, id)
            await ctx.reply(f"Successfully edited **Task ID -** `{id}`")

    @todo.command(
        name = "remove",
        brief = "Removes Task",
        aliases = ["finished", "done"])
    async def todo_remove(self, ctx : commands.context, *, id : int):
        """Remove a particular task."""
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{ctx.clean_prefix}{ctx.command}` for the `{ctx.command}` command <:SarahPray:920484222421045258>"
        async def yes(ui : discord.ui.View, interaction : discord.Interaction, button : discord.ui.button):
            if interaction.user != ctx.author:
                return await interaction.response.send_message(content = f"{pain}", ephemeral = True)
            for view in ui.children:
                view.disabled = True
                view.style = ButtonStyle.grey  
            if id != await self.bot.db.fetchval(f"SELECT * FROM todo WHERE task_id = $1 AND user_name = $2", id, ctx.author.name):
                await interaction.response.defer()
                return await ui.response.edit(content = f"<:GeraltRightArrow:904740634982760459> **Task ID ** `{id}` : is a task either which you do not own or is not present in the database <a:IPat:933295620834336819>", view = ui)
            else:
                await interaction.response.defer()
                await self.bot.db.execute(f"DELETE FROM todo WHERE task_id = $1", id)
                await ui.response.edit(content = f"Successfully removed **Task ID -** `{ui}` <:HaroldSaysOkay:907110916104007681>", view = ui)

        async def no(ui : discord.ui.View, interaction : discord.Interaction, button : discord.ui.button):
            if interaction.user != ctx.author:
                return await interaction.response.send_message(content = f"{pain}", ephemeral = True)
            for view in ui.children:
                view.disabled = True  
                view.style  =   ButtonStyle.grey
            await interaction.response.defer()
            await ui.response.edit(content = f"Okay then, I haven't removed Task ID - `{id}` from your list <:DuckSip:917006564265705482>", view = ui)
        
        Interface.Confirmation.response    =    await ctx.reply(f"Are you sure you want to remove Task ID - `{id}` from your list <:BallManHmm:933398958263386222>", view = Interface.Confirmation(ctx, yes, no))    

    @todo.command(
        name = "clear",
        brief = "Delete Todo Tasks.",
        aliases = ["delete", "del", "cl"])
    async def todo_clear(self, ctx : commands.context):
        """Delete your entire todo list."""
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{ctx.clean_prefix}{ctx.command}` for the `{ctx.command}` command <:SarahPray:920484222421045258>"
        total = await self.bot.db.fetch(f"SELECT * FROM todo WHERE user_id = $1", ctx.author.id)
        if total == 0:
            await ctx.reply("You currently have `0` tasks present. To start listing out tasks, run `{ctx.clean_prefix}todo add <task>`")
        else:
            async def yes(ui : discord.ui.View, interaction : discord.Interaction, button : discord.ui.button):
                if button.user != ctx.author:
                    return await interaction.response.send_message(content = f"{pain}", ephemeral = True)
                fetch_task = await self.bot.db.execute(f"DELETE FROM todo WHERE user_id = $1", ctx.author.id)
                for view in ui.children:
                    view.disabled = True  
                    view.style = ButtonStyle.grey
                if not fetch_task:
                    await interaction.response.defer()
                    await ui.response.edit("You currently have `0` tasks present. To start listing out tasks, run `{ctx.clean_prefix}todo add <TASK>` <a:CoffeeSip:907110027951742996>", view = ui)
                else:
                    await interaction.response.defer()
                    await ui.response.edit(content = f"Successfully deleted `{len(total)}` tasks from your list <:ICool:940786050681425931>.", view = ui)
            
            async def no(ui : discord.ui.View, interaction : discord.Interaction, button : discord.ui.button):
                if button.user != ctx.author:
                    return await interaction.response.send_message(content = f"{pain}", ephemeral = True)
                for view in ui.children:
                    view.disabled = True  
                    view.style  =   ButtonStyle.grey
                await interaction.response.defer()
                await ui.response.edit(content = "Okay then, I haven't deleted any `tasks` from your list <a:IEat:940413722537644033>", view = ui)
        
        Interface.Confirmation.response    =    await ctx.reply(f"Are you sure you want to delete a total of `{len(total)}` tasks in your list <a:IThink:933315875501641739>", view = Interface.Confirmation(ctx, yes, no))

    @commands.command(
        name = "spotify",
        brief = "Get Spotify Info.",
        aliases = ["sp", "spot"])
    async def spotify(self, ctx : commands.context, *, user : typing.Union[discord.Member, discord.User] = None):
        """Get Information on what the user is listening to."""
        user = user or ctx.author
        spotify = discord.utils.find(lambda sp : isinstance(sp, discord.Spotify), user.activities)
        if spotify is None:
            if user ==  ctx.author:
                return await ctx.reply("You are not listening to Spotify right now.")
            else:
                return await ctx.reply(f"**{user}** is not listening to any song on **Spotify** right now.")
        else:
            spotify_emb = discord.Embed(
                title = f":scroll: {user}'s Spotify Status",
                description = f"They are listening to [**{spotify.title}**]({spotify.track_url}) by - **{spotify.artist}**",
                colour = self.bot.colour)
            spotify_emb.add_field(
                name = "Song Information :",
                value = f"> **<:ReplyContinued:930634770004725821> - Name :** [**{spotify.title}**]({spotify.track_url}) (`{spotify.track_id}`)\n" \
                        f"> **<:ReplyContinued:930634770004725821> - Album :** {spotify.album}\n" \
                        f"> **<:Reply:930634822865547294> - Duration :** {humanize.precisedelta(spotify.duration)}")
            spotify_emb.set_thumbnail(url = spotify.album_cover_url)
        await ctx.send(embed = spotify_emb)
        
async def setup(bot):
    await bot.add_cog(Utility(bot))