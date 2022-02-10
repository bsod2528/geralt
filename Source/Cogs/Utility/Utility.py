from click import command
import disnake
import humanize
import asyncpg as PSQL

from disnake.ext import commands

import Source.Kernel.Views.Interface as Interface
import Source.Kernel.Utilities.Flags as FLAGS
from Source.Kernel.Views.Paginator import Paginator

class Utility(commands.Cog):
    """Utility Commands"""
    def __init__(self, bot):
        self.bot    =   bot

    # Get user's PFP
    @commands.command(
        name    =   "avatar",
        aliases =   ["pfp", "pp", "dp", "av"],
        brief   =   "View a persons PFP")
    async def avatar(self, ctx, *, USER : disnake.Member = None):
        """See the user's PFP in an enlarged manner"""
        USER    =   USER or ctx.author
        PFP_EMB =   disnake.Embed(
            title   =   f"{str(USER)}'s Avatar",
            url =   USER.display_avatar.url,
            colour = self.bot.colour)
        AVATAR  = USER.display_avatar.with_static_format("png")
        PFP_EMB.set_image(url = AVATAR)
        PFP_EMB.timestamp = disnake.utils.utcnow()
        await ctx.reply(embed = PFP_EMB, mention_author = False, view = Interface.PFP(ctx, self.bot))
    
    # Get user's information
    @commands.command(
        name    =   "userinfo",
        aliases =   ["user", "ui"],
        brief   =   "Get user information")
    async def userinfo(self, ctx, *, USER : disnake.Member = None):
        """Get entire details about a user."""
        USER    =   USER or ctx.author
        ROLES   =   ""
        for ROLE in USER.roles:
            if ROLE is ctx.guild.default_role: continue
            ROLES   =   f"{ROLES} {ROLE.mention}"
        if ROLES    !=  "":
            ROLES   =   f"{ROLES}"
        FETCHED_USER    =   await ctx.bot.fetch_user(USER.id)
        PERMISSIONS     =   FLAGS.USER_PERMS(USER.guild_permissions)
        if PERMISSIONS:
            PERMS   =   f"{' **|** '}".join(PERMISSIONS)
        AVATAR  =   USER.display_avatar.with_static_format("png")
        ACTIVITY = disnake.utils.find(lambda act: isinstance(act, disnake.CustomActivity), USER.activities)
        ACTIVITY_HOLDER = f"`{disnake.utils.remove_markdown(ACTIVITY.name)}`" if ACTIVITY and ACTIVITY.name else f'`{USER}` has no activity at the moment.'

        GENERAL_EMB =   disnake.Embed(
            title   =   f":scroll: {USER}'s Information",
            colour  =   USER.colour)
        GENERAL_EMB.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> General Info :",
            value   =   f"> **<:ReplyContinued:930634770004725821> - Name :** {USER.mention} \n" \
                        f"> **<:ReplyContinued:930634770004725821> - Nickname :** {(USER.nick) or 'No nickname set'} \n" \
                        f"> **<:ReplyContinued:930634770004725821> - Discriminator :** `#{USER.discriminator}` \n"
                        f"> **<:Reply:930634822865547294> - Identification No. :** `{USER.id}` \n")
        GENERAL_EMB.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> Account Info :",
            value   =   f"> **<:ReplyContinued:930634770004725821> - Created on :**{self.bot.DT(USER.created_at, style = 'D')} ({self.bot.DT(USER.created_at, style = 'R')}) \n" \
                        f"> **<:Reply:930634822865547294> - Joined Guild on :**{self.bot.DT(USER.joined_at, style = 'D')} ({self.bot.DT(USER.joined_at, style = 'R')})\n",
            inline  = False)
        GENERAL_EMB.set_thumbnail(url = AVATAR)
        GENERAL_EMB.timestamp = disnake.utils.utcnow()

        GUILD_EMB   =   disnake.Embed(
            title   =   f":scroll: {USER} in {ctx.guild}",
            colour  =   USER.colour)
        GUILD_EMB.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> Permissions Present :",
            value   =   f"> **<:Reply:930634822865547294> -** {PERMS}")
        GUILD_EMB.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> Top Most Role :",
            value   =   f"> **<:Reply:930634822865547294> -** {USER.top_role.mention}",
            inline  =   False)
        GUILD_EMB.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> All Roles Present :",
            value   =   f"> **<:Reply:930634822865547294> -** {ROLES}",
            inline  =   False)
        GUILD_EMB.set_thumbnail(url = AVATAR)
        GUILD_EMB.timestamp = disnake.utils.utcnow()

        MISC_EMB    =   disnake.Embed(
            title   =   f":scroll: {USER} - Misc. Information",
            colour  =   USER.colour)
        MISC_EMB.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> Badges Present :",
            value   =   f"> **<:Reply:930634822865547294> - **{FLAGS.USER_BADGES(USER= USER, FETCH_USER = FETCHED_USER) if FLAGS.USER_BADGES(USER= USER, FETCH_USER = FETCHED_USER) else '`No Badges Present`'}")
        MISC_EMB.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> Accent Colours :",
            value   =   f"> **<:ReplyContinued:930634770004725821> - Banner Colour :** `{str(FETCHED_USER.accent_colour).upper()}` \n" \
                        f"> **<:Reply:930634822865547294> - Guild Role Colour :** `{USER.color if USER.color is not disnake.Color.default() else 'Default'}`",
            inline  =   False)  
        MISC_EMB.add_field(
            name    =   "Activity :",
            value   =   f"> **<:Reply:930634822865547294> -** {ACTIVITY_HOLDER}",
            inline  =   False)
        MISC_EMB.set_thumbnail(url = AVATAR)
        MISC_EMB.timestamp = disnake.utils.utcnow()
        
        PFP_EMB =   disnake.Embed(
            title = f":scroll: {USER}'s PFP",
            description =   f"[**JPG Format**]({USER.display_avatar.with_static_format('jpg')}) **|** [**PNG Format**]({USER.display_avatar.with_static_format('png')}) **|** [**WEBP Format**]({USER.display_avatar.with_static_format('webp')})",
            colour = USER.colour)
        PFP_EMB.set_image(url = AVATAR)
        PFP_EMB.timestamp = disnake.utils.utcnow()

        EMBED_LIST = [GENERAL_EMB, GUILD_EMB, MISC_EMB, PFP_EMB]
        View = Paginator(ctx, EMBEDS = EMBED_LIST)
        await ctx.trigger_typing()
        await ctx.reply(embed = EMBED_LIST[0], view = View, allowed_mentions = self.bot.Mention)

    @commands.command(
        name    =   "serverinfo",
        aliases =   ["si", "gi"],
        brief   =   "Get guild information")
    @commands.guild_only()
    async def server_info(self, ctx):
        """Get entire details about the guild."""
        USER_STATUS =   [len(list(filter(lambda U   :   str(U.status) == 'online', ctx.guild.members))),
                        len(list(filter(lambda U    :   str(U.status) == 'idle', ctx.guild.members))),
                        len(list(filter(lambda U    :   str(U.status) == 'dnd', ctx.guild.members))),
                        len(list(filter(lambda U    :   str(U.status) == 'offline', ctx.guild.members)))]

        GENERAL_EMB =   disnake.Embed(
            title   =   f":scroll: {ctx.guild.name}'s Information",
            colour  =   self.bot.colour)
        GENERAL_EMB.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> General Information :",
            value   =   f"> **<:ReplyContinued:930634770004725821> - <a:Owner:905750348457738291> Owner :** {ctx.guild.owner.mention} (`{ctx.guild.owner.id}`) \n" \
                        f"> **<:ReplyContinued:930634770004725821> - <a:Users:905749451350638652> No. of Roles :** `{len(ctx.guild.roles)}` \n" \
                        f"> **<:ReplyContinued:930634770004725821> - <a:Info:905750331789561856> Identification No. :** `{ctx.guild.id}` \n" \
                        f"> **<:ReplyContinued:930634770004725821> - <a:Verify:905748402871095336> Verification Level :** {str(ctx.guild.verification_level).replace('_', ' ').replace('`NONE`', '`NILL`').title()} \n" \
                        f"> **<:Reply:930634822865547294> - <:WinFileBruh:898571301986373692> File Transfer Limit:** `{humanize.naturalsize(ctx.guild.filesize_limit)}`")
        GENERAL_EMB.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> Initialisation :",
            value   =   f"> **<:ReplyContinued:930634770004725821> - <a:Woo:905754435379163176> Made On :** {self.bot.DT(ctx.guild.created_at)} \n" \
                        f"> **<:Reply:930634822865547294> - <:ISus:915817563307515924> Media Filteration :** For `{str(ctx.guild.explicit_content_filter).replace('_',' ').replace('`NONE`', '`NILL`').title()}` \n",
            inline  =   False)
        GENERAL_EMB.set_thumbnail(url = ctx.guild.icon.url)
        GENERAL_EMB.timestamp = disnake.utils.utcnow()

        OTHER_EMB   =   disnake.Embed(
            title   =   f":scroll: {ctx.guild.name}'s Other Information",
            colour  =   self.bot.colour)
        OTHER_EMB.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> Channel Information :",
            value   =   f"> **<:ReplyContinued:930634770004725821> - <:Channel:905674680436944906> Text :** `{len(ctx.guild.text_channels)}` \n" \
                        f"> **<:ReplyContinued:930634770004725821> - <:Voice:905746719034187796> Voice :** `{len(ctx.guild.voice_channels)}` \n" \
                        f"> **<:ReplyContinued:930634770004725821> - <a:Thread:905750997706629130> Threads :** `{len(ctx.guild.threads)}` \n" \
                        f"> **<:Reply:930634822865547294> - <:StageChannel:905674422839554108> Stage :** `{len(ctx.guild.stage_channels)}` \n",
            inline  =   False)
        OTHER_EMB.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> Emotes Present :",
            value   =   f"> **<:ReplyContinued:930634770004725821> - <a:IThink:933315875501641739> Animated :** `{len([ANI for ANI in ctx.guild.emojis if ANI.animated])}` / `{ctx.guild.emoji_limit}` \n" \
                        f"> **<:Reply:930634822865547294> - <:BallManHmm:933398958263386222> Non - Animated :** `{len([NON_ANI for NON_ANI in ctx.guild.emojis if not NON_ANI.animated])}` / `{ctx.guild.emoji_limit}`",
            inline  =   False)
        OTHER_EMB.set_thumbnail(url = ctx.guild.icon.url)
        OTHER_EMB.timestamp =   disnake.utils.utcnow()

        USER_EMB    =   disnake.Embed(
            title   =   f":scroll: {ctx.guild.name}'s Users Information",
            colour  =   self.bot.colour)
        USER_EMB.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> No. of User :",
            value   =   f"> **<:ReplyContinued:930634770004725821> - <a:HumanBro:905748764432662549> No. of Humans :** `{len(list(filter(lambda U : U.bot is False, ctx.guild.members)))}` \n" \
                        f"> **<:ReplyContinued:930634770004725821> - <a:BotLurk:905749164355379241> No. of Bots :** `{len(list(filter(lambda U : U.bot, ctx.guild.members)))}` \n" \
                        f"> **<:Reply:930634822865547294> - <a:Users:905749451350638652> Total :** `{ctx.guild.member_count}` \n",
            inline  =   False)
        USER_EMB.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> Activity Information :",
            value   =   f"> **<:ReplyContinued:930634770004725821> - <:Online:905757053119766528> Online :** `{USER_STATUS[0]}` \n" \
                        f"> **<:ReplyContinued:930634770004725821> - <:Idle:905757063064453130> Idle :** `{USER_STATUS[1]}` \n" \
                        f"> **<:ReplyContinued:930634770004725821> - <:DnD:905759353141874709> Do Not Disturb :** `{USER_STATUS[2]}` \n" \
                        f"> **<:Reply:930634822865547294> - <:Offline:905757032521551892> Offline :** `{USER_STATUS[3]}`",
            inline  =   False)
        USER_EMB.set_thumbnail(url = ctx.guild.icon.url)
        USER_EMB.timestamp = disnake.utils.utcnow()
    
        ICON_EMB    =   disnake.Embed(
            title   =   f":scroll: {ctx.guild.name}'s Icon",
            description =   f"[**JPG Format**]({ctx.guild.icon.with_static_format('jpg')}) **|** [**PNG Format**]({ctx.guild.icon.with_static_format('png')}) **|** [**WEBP Format**]({ctx.guild.icon.with_static_format ('webp')})",
            colour  =   self.bot.colour)
        ICON_EMB.set_image(url = ctx.guild.icon.url)
        ICON_EMB.timestamp = disnake.utils.utcnow()

        EMBED_LIST  =   [GENERAL_EMB, OTHER_EMB, USER_EMB, ICON_EMB]
        View = Paginator(ctx, EMBEDS = EMBED_LIST)
        await ctx.trigger_typing()
        await ctx.reply(embed = EMBED_LIST[0], view = View, allowed_mentions = self.bot.Mention)

    @commands.group(
        name    =   "todo",
        aliases =   ["td"],
        brief   =   "List User's Todo List.")
    async def todo(self, ctx):
        """Sends Todo sub - commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @todo.command(
        name    =   "add",
        brief   =   "Add item to your list.")
    async def todo_add(self, ctx, *, TASK : str):
        """Add tasks to your todo list."""
        await self.bot.DB.execute(f"INSERT INTO todo (user_name, user_id, discriminator, task, task_created_at, url) VALUES ($1, $2, $3, $4, $5, $6) RETURNING task_id", ctx.author.name, ctx.author.id, ctx.author.discriminator, TASK, ctx.message.created_at, ctx.message.jump_url)
        TASK_ID =   await self.bot.DB.fetchval(f"SELECT task_id FROM todo WHERE task = $1", TASK)
        await ctx.reply(f"Successfully added task.\n<:Reply:930634822865547294> **Task ID -** `{TASK_ID}`")
    
    @todo.command(
        name    =   "list",
        aliases =   ["show"],
        brief   =   "See your todo list.")  
    async def todo_list(self, ctx):
        """See your entire todo list."""
        TODO_LIST   =   await self.bot.DB.fetch(f"SELECT * FROM todo WHERE user_id = $1", ctx.author.id)
        TASK_LIST   =   []
        SERIAL_NO   =   0
        for TASKS in TODO_LIST:
            TASK_LIST.append(f"> [**{SERIAL_NO}. -**]({TASKS['url']}) {TASKS['task']}" f"\n> <:Reply:930634822865547294> **ID :** `{TASKS['task_id']}` - ({self.bot.DT(TASKS['task_created_at'], style = 'R')})\n")
            SERIAL_NO   +=  1
        
        if not TODO_LIST:
            await ctx.reply(f"You currently have `0` tasks present. To start listing out tasks, run `{ctx.clean_prefix}todo add <TASK>` <a:LifeSucks:932255208044650596>")
        
        else:
            TODO_LIST_EMB   =   disnake.Embed(
            title   =   f"{ctx.author}'s Todo List :",
            description =   f"".join(TASK for TASK in TASK_LIST),
            colour  =   self.bot.colour)
            TODO_LIST_EMB.set_thumbnail(url = ctx.author.display_avatar.url)
            TODO_LIST_EMB.set_footer(text = f"Run {ctx.clean_prefix}todo for more sub - commands.")
            TODO_LIST_EMB.timestamp =   disnake.utils.utcnow()
            await ctx.reply(embed = TODO_LIST_EMB, mention_author = False)

    @todo.command(
        name    =   "edit",
        brief   =   "Edit task")    
    async def todo_edit(self, ctx, ID : int, *, EDITED : commands.clean_content):
        """Edit a particular task."""

        if ID != await self.bot.DB.fetchval(f"SELECT * FROM todo WHERE task_id = $1 AND user_name = $2", ID, ctx.author.name):
            await ctx.reply(f"<:GeraltRightArrow:904740634982760459> **Task ID -** `{ID}` - is a task either which you do not own or is not present in the database <:DutchySMH:930620665139191839>")
        else:
            await self.bot.DB.execute(f"UPDATE todo SET task = $1, url = $2, task_created_at = $3 WHERE task_id = $4", EDITED, ctx.message.jump_url, ctx.message.created_at, ID)
            await ctx.reply(f"Successfully edited **Task ID -** `{ID}`")

    @todo.command(
        name    =   "remove",
        brief   =   "Removes Task")
    async def todo_remove(self, ctx, *, ID : int):
        """Remove a particular task."""
        async def YES(UI : disnake.ui.View, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction):
            if INTERACTION.user != ctx.author:
                return await INTERACTION.response.send_message(content = f"{Interface.PAIN}", ephemeral = True)
            
            if ID != await self.bot.DB.fetchval(f"SELECT * FROM todo WHERE task_id = $1 AND user_name = $2", ID, ctx.author.name):
                return await UI.response.edit(content = f"<:GeraltRightArrow:904740634982760459> **Task ID -** `{ID}` : is a task either which you do not own or is not present in the database <a:IPat:933295620834336819>", view = None)
            else:
                await self.bot.DB.execute(f"DELETE FROM todo WHERE task_id = $1", ID)
                await UI.response.edit(content = f"Successfully removed **Task ID -** `{ID}` <:HaroldSaysOkay:907110916104007681>", view = None)

        async def NO(UI : disnake.ui.View, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction):
            if INTERACTION.user != ctx.author:
                await INTERACTION.response.send_message(content = f"{Interface.PAIN}", ephemeral = True)
                return
            await UI.response.edit(content = f"Okay then, I haven't removed Task ID - `{ID}` from your list <:DuckSip:917006564265705482>", view = None)
        
        Interface.Confirmation.response    =    await ctx.reply(f"Are you sure you want to remove Task ID - `{ID}` from your list <:BallManHmm:933398958263386222>", view = Interface.Confirmation(YES, NO))    

    @todo.command(
        name    =   "clear",
        aliases =   ["delete", "del", "cl"],
        brief   =   "Delete Todo Tasks.")
    async def todo_clear(self, ctx):
        """Delete your entire todo list."""
        TOTAL   =   await self.bot.DB.fetch(f"SELECT FROM todo WHERE user_id = $1", ctx.author.id)
        if TOTAL == 0:
            await ctx.reply("You currently have `0` tasks present. To start listing out tasks, run `{ctx.clean_prefix}todo add <TASK>`")
        else:
            async def YES(UI : disnake.ui.View, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction):
                DELETE_LIST =   await self.bot.DB.execute(f"DELETE FROM todo WHERE user_id = $1", ctx.author.id)
                if INTERACTION.user != ctx.author:
                    return await INTERACTION.response.send_message(content = f"{Interface.PAIN}", ephemeral = True)
                
                if not DELETE_LIST:
                    await UI.response.edit("You currently have `0` tasks present. To start listing out tasks, run `{ctx.clean_prefix}todo add <TASK>` <a:CoffeeSip:907110027951742996>", view = None)
                else:
                    await UI.response.edit(content = f"Successfully deleted `{len(TOTAL)}` tasks from your list <:ICool:940786050681425931>.", view = None)
            
            async def NO(UI : disnake.ui.View, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction):
                if INTERACTION.user != ctx.author:
                    return await INTERACTION.response.send_message(content = f"{Interface.PAIN}", ephemeral = True)
                await UI.response.edit(content = "Okay then, I haven't deleted any `tasks` from your list <a:IEat:940413722537644033>", view = None)
        
            Interface.Confirmation.response    =    await ctx.reply(f"Are you sure you want to delete a total of `{len(TOTAL)}` tasks in your list <a:IThink:933315875501641739>", view = Interface.Confirmation(YES, NO))

def setup(bot):
    bot.add_cog(Utility(bot))