import disnake
import humanize

from disnake.ext import commands

import Source.Kernel.Views.Interface as UI
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
        await ctx.reply(embed = PFP_EMB, mention_author = False, view = UI.PFP(ctx, self.bot))
    
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

def setup(bot):
    bot.add_cog(Utility(bot))