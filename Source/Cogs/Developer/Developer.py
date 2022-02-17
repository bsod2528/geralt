import io
import time
import asyncpg
import disnake
import asyncio
import textwrap
import humanize
import traceback
import contextlib

from disnake.ext import commands
from disnake.enums import ButtonStyle

from __main__ import KERNEL
import Source.Kernel.Views.Paginator as Paginator
import Source.Kernel.Utilities.Crucial as CRUCIAL
from Source.Kernel.Views.Interface import Confirmation, PAIN

# Class for buttons in eval command.
class EvalButtons(disnake.ui.View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx    =   ctx
    
    @disnake.ui.button(label = "Traceback", style = ButtonStyle.gray)
    async def TRACEBACK(self, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction):
        TB_EMB  =   disnake.Embed(
            title   =   "Errors Going Boing",
            description =   f"{Exception.__class__.__name__} -> {Exception}",
            colour  =   self.bot.colour)
        await INTERACTION.response.send_message(embed = TB_EMB, ephemeral = True)

class Developer(commands.Cog):
    """Developer Commands"""
    def __init__(self, bot):
        self.bot = bot
    
    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    # Shuts the bot down in a friendly manner.
    @commands.command(
        name    =   "die", 
        aliases =   ["snap"], 
        brief   =   "Eternal Sleep")
    @commands.is_owner()
    async def die(self, ctx):
        """Sends the bot to eternal sleep"""
        async def YES(UI : disnake.ui.View, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction):
            if INTERACTION.user != ctx.author:
                await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True)
            for View in UI.children:
                View.disabled = True
                View.style  =   ButtonStyle.grey
            await INTERACTION.response.edit_message(content = "Okay then, I shall go to eternal sleep", view = UI, allowed_mentions = self.bot.Mention)
            UI.stop()
            await self.bot.close()

        async def NO(UI : disnake.ui.View, BUTTON: disnake.ui.button, INTERACTION : disnake.Interaction):
            if INTERACTION.user != ctx.author:
                await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True)
            for View in UI.children:
                View.disabled = True
                View.style  =   ButtonStyle.grey
            await INTERACTION.response.edit_message(content = "Seems like I'm gonna be alive for a bit longer",view = UI, allowed_mentions = self.bot.Mention)
            UI.stop()
        Confirmation.response    = await ctx.reply("Do you want to kill me?", view = Confirmation(YES, NO), allowed_mentions = self.bot.Mention)
    
    # Evaluate command for running both asynchronous and sychronous programs.
    @commands.command(
        name    =   "eval",
        aliases =   ["e"],
        brief   =   "Run Code")
    @commands.is_owner()
    async def eval(self, ctx, *, BODY : str):
        """Running both asynchronous and sychronous programs"""
        ENVIRONTMENT = {
            "self"      :   self,
            "disnake"   :   disnake,
            "bot"       :   self.bot,
            "ctx"       :   ctx,
            "message"   :   ctx.message,
            "author"    :   ctx.author,
            "guild"     :   ctx.guild,
            "channel"   :   ctx.channel,
        }

        ENVIRONTMENT.update(globals())
        if BODY.startswith( "```" ) and BODY.endswith( "```" ):
            BODY    =   "\n".join(BODY.split("\n")[1:-1])
        BODY    =   BODY.strip("` \n")
        STDOUT  =   io.StringIO()
        COMPILE =   f"async def func():\n{textwrap.indent(BODY, '  ')}"
        try:    
            exec(COMPILE, ENVIRONTMENT)
        except Exception as EXCEPT:
            EMB = disnake.Embed(
                description = f"```py\n{EXCEPT.__class__.__name__} --> {EXCEPT}\n```",
                colour = self.bot.colour)
            return await ctx.send(embed = EMB)
        FUNC    =   ENVIRONTMENT["func"]
        try:
            with contextlib.redirect_stdout(STDOUT):
                RETUNRED_VALUE  =   await FUNC()
        except Exception as EXCEPT:
            VALUE   =   STDOUT.getvalue()
            EMB = disnake.Embed(
                description = f"```py\n{VALUE}{traceback.format_exc()}\n```",
                color = 0x2F3136)
            message = await ctx.send(embed = EMB)
            await ctx.message.add_reaction('<:WinUnheck:898572376147623956>')
        else:
            VALUE   =   STDOUT.getvalue()
            try:
                await ctx.message.add_reaction('<:WinCheck:898572324490604605>')
            except:
                pass
            if RETUNRED_VALUE is None:
                if VALUE:
                    EMB =   disnake.Embed(
                        description =   f"```py\n{VALUE}\n```",
                        colour      =   self.bot.colour)
                    await ctx.send(embed = EMB, mention_author = False)
            else:
                EMB =   disnake.Embed(
                    description = f"```py\n{VALUE}{RETUNRED_VALUE}\n```",
                    colour = self.bot.colour)
                await ctx.send(embed = EMB, mention_author = False)

    # Loads extension of choice
    @commands.command(
        name    =   "load",
        aliases =   ["l"],
        brief   =   "Loads Cog")
    @commands.is_owner()
    async def load(self, ctx, *, COG : str):
        """Loads the Extension mentioned."""
        async def YES(UI : disnake.ui.View, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction):
            if INTERACTION.user != ctx.author:
                return await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True)
            for View in UI.children:
                View.disabled   =   True
                View.style  =   ButtonStyle.grey
            try:
                self.bot.load_extension(f"Source.Cogs.{COG}")
            except Exception as EXCEPT:
                await UI.response.edit(content = f"Couldn't load **{COG}** due to : __ {EXCEPT} __ : <:Pain:911261018582306867>", view = UI, allowed_mentions = self.bot.Mention)
            else:
                await UI.response.edit(content = f"Loaded : **{COG}** <:RavenPray:914410353155244073>", view = UI, allowed_mentions = self.bot.Mention)
            UI.stop()

        async def NO(UI : disnake.ui.View, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction):
            if INTERACTION.user != ctx.author:
                return await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True)
            for View in UI.children:
                    View.disabled   =   True
                    View.style  =   ButtonStyle.grey
            await UI.response.edit(content = f"Seems like you don't want to load **{COG}**.\nNot my problem <:AkkoHmm:907105376523153458>", view = UI, allowed_mentions = self.bot.Mention)
        Confirmation.response    = await ctx.reply(f"Do you want to load : **{COG}** <:Sus:916955986953113630>", view = Confirmation(YES, NO), allowed_mentions = self.bot.Mention)

    # Unloads extension of choice
    @commands.command(
        name    =   "unload",
        aliases =   ["ul"],
        brief   =   "Unloads Cog")
    @commands.is_owner()
    async def unload(self, ctx, *, COG : str):
        """Unloads the Extension mentioned."""
        async def YES(UI : disnake.ui.View, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction):
            if INTERACTION.user != ctx.author:
                return await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True)
            for View in UI.children:
                    View.disabled   =   True
                    View.style  =   ButtonStyle.grey
            try:
                self.bot.unload_extension(f"Source.Cogs.{COG}")
            except Exception as EXCEPT:
                await UI.response.edit(content = f"Couldn't unload **{COG}** due to : __ {EXCEPT} __ : <:Pain:911261018582306867>", view = UI, allowed_mentions = self.bot.Mention)
            else:
                await UI.response.edit(content = f"Unloaded : **{COG}** <:RavenPray:914410353155244073>", view = UI, allowed_mentions = self.bot.Mention)
            UI.stop()

        async def NO(UI : disnake.ui.View, BUTTON : disnake.ui.button, INTERACTION : disnake.Interaction):
            if INTERACTION.user != ctx.author:
                return await INTERACTION.response.send_message(content = f"{PAIN}", ephemeral = True)
            for View in UI.children:
                    View.disabled   =   True
                    View.style  =   ButtonStyle.grey
            await UI.response.edit(content = f"Seems like you don't want to unload **{COG}**.\nNot my problem <:AkkoHmm:907105376523153458>", view = UI, allowed_mentions = self.bot.Mention)
        async with ctx.typing():
            await asyncio.sleep(0.2)
        Confirmation.response    = await ctx.reply(f"Do you want to unload : **{COG}** <:Sus:916955986953113630>", view = Confirmation(YES, NO), allowed_mentions = self.bot.Mention)
    
    # Reloads extension of choice
    @commands.command(
        name    =   "reload",
        aliases =   ["rl"],
        brief   =   "Reloads Cog")
    @commands.is_owner()
    async def reload(self, ctx, *, COG : str):
        """Reloads the Extension mentioned."""
        try:
            self.bot.reload_extension(f"Source.Cogs.{COG}")
            await ctx.reply(f"**{COG}** : Successfully Reloaded <:RavenPray:914410353155244073>", allowed_mentions = self.bot.Mention)
        except Exception as EXCEPT:
            await ctx.reply(f"Couldn't reload **{COG}** : `{EXCEPT}`", allowed_mentions = self.bot.Mention)
    
    # Group of Commands used for changing presence.
    @commands.group(
        name    =   "dev",
        aliases =   ["devmode"],
        brief   =   "Simple Dev Stuff")
    @commands.is_owner()
    async def dev(self, ctx):
        """Simple commands for dev to do"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @dev.command(
        name    =   "total-guilds",
        aliases =   ["tg"],
        brief   =   "Sends Guild List")
    async def total_guilds(self, ctx):
        """Sends the entire guild list."""
        await ctx.reply(f"Currently in `{len(self.bot.guilds)}` Guilds.", allowed_mentions = self.bot.Mention)
        await ctx.send(f" ".join([f"> **- {g.name} :** {g.owner.mention} (`{g.id}`)\n" for g in self.bot.guilds]) + "", allowed_mentions = self.bot.Mention)

    @dev.command(
        name    =   "on",
        brief   =   "Sets Status Offline")
    async def on(self, ctx):
        """Sets the bot status as Invisible"""
        await self.bot.change_presence(
            status  =   disnake.Status.invisible)
        await ctx.message.add_reaction("<:Offline:905757032521551892>")
    
    @dev.command(
        name    =   "off",
        brief   =   "Sets Status Idle")
    async def off(self, ctx):
        """Sets the bot status as Idle"""
        await self.bot.change_presence(
            status  =   disnake.Status.idle,
            activity    =   disnake.Activity(type = disnake.ActivityType.listening, name = ".ghelp"))
        await ctx.message.add_reaction("<:Idle:905757063064453130>")
    
    @commands.command(
        name    =   "guildfetch",
        aliases =   ["fg"],
        brief   =   "Get guild information")
    @commands.is_owner()
    async def fetch_guild(self, ctx, *, GUILD : disnake.Guild):
        """Get entire details about the guild."""
        USER_STATUS =   [len(list(filter(lambda U   :   str(U.status) == 'online', GUILD.members))),
                        len(list(filter(lambda U    :   str(U.status) == 'idle', GUILD.members))),
                        len(list(filter(lambda U    :   str(U.status) == 'dnd', GUILD.members))),
                        len(list(filter(lambda U    :   str(U.status) == 'offline', GUILD.members)))]

        GENERAL_EMB =   disnake.Embed(
            title   =   f":scroll: {GUILD.name}'s Information",
            colour  =   self.bot.colour)
        GENERAL_EMB.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> General Information :",
            value   =   f"> **<:ReplyContinued:930634770004725821> - <a:Owner:905750348457738291> Owner :** {GUILD.owner.mention} (`{GUILD.owner.id}`) \n" \
                        f"> **<:ReplyContinued:930634770004725821> - <a:Users:905749451350638652> No. of Roles :** `{len(GUILD.roles)}` \n" \
                        f"> **<:ReplyContinued:930634770004725821> - <a:Info:905750331789561856> Identification No. :** `{GUILD.id}` \n" \
                        f"> **<:ReplyContinued:930634770004725821> - <a:Verify:905748402871095336> Verification Level :** {str(GUILD.verification_level).replace('_', ' ').replace('`NONE`', '`NILL`').title()} \n" \
                        f"> **<:Reply:930634822865547294> - <:WinFileBruh:898571301986373692> File Transfer Limit:** `{humanize.naturalsize(GUILD.filesize_limit)}`")
        GENERAL_EMB.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> Initialisation :",
            value   =   f"> **<:ReplyContinued:930634770004725821> - <a:Woo:905754435379163176> Made On :** {self.bot.DT(GUILD.created_at)} \n" \
                        f"> **<:Reply:930634822865547294> - <:ISus:915817563307515924> Media Filteration :** For `{str(GUILD.explicit_content_filter).replace('_',' ').replace('`NONE`', '`NILL`').title()}` \n",
            inline  =   False)
        GENERAL_EMB.set_thumbnail(url = GUILD.icon.url)
        GENERAL_EMB.timestamp = disnake.utils.utcnow()

        OTHER_EMB   =   disnake.Embed(
            title   =   f":scroll: {GUILD.name}'s Other Information",
            colour  =   self.bot.colour)
        OTHER_EMB.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> Channel Information :",
            value   =   f"> **<:ReplyContinued:930634770004725821> - <:Channel:905674680436944906> Text :** `{len(GUILD.text_channels)}` \n" \
                        f"> **<:ReplyContinued:930634770004725821> - <:Voice:905746719034187796> Voice :** `{len(GUILD.voice_channels)}` \n" \
                        f"> **<:ReplyContinued:930634770004725821> - <a:Thread:905750997706629130> Threads :** `{len(GUILD.threads)}` \n" \
                        f"> **<:Reply:930634822865547294> - <:StageChannel:905674422839554108> Stage :** `{len(GUILD.stage_channels)}` \n",
            inline  =   False)
        OTHER_EMB.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> Emotes Present :",
            value   =   f"> **<:ReplyContinued:930634770004725821> - <a:IThink:933315875501641739> Animated :** `{len([ANI for ANI in GUILD.emojis if ANI.animated])}` / `{GUILD.emoji_limit}` \n" \
                        f"> **<:Reply:930634822865547294> - <:BallManHmm:933398958263386222> Non - Animated :** `{len([NON_ANI for NON_ANI in GUILD.emojis if not NON_ANI.animated])}` / `{GUILD.emoji_limit}`",
            inline  =   False)
        OTHER_EMB.set_thumbnail(url = GUILD.icon.url)
        OTHER_EMB.timestamp =   disnake.utils.utcnow()

        USER_EMB    =   disnake.Embed(
            title   =   f":scroll: {GUILD.name}'s Users Information",
            colour  =   self.bot.colour)
        USER_EMB.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> No. of User :",
            value   =   f"> **<:ReplyContinued:930634770004725821> - <a:HumanBro:905748764432662549> No. of Humans :** `{len(list(filter(lambda U : U.bot is False, GUILD.members)))}` \n" \
                        f"> **<:ReplyContinued:930634770004725821> - <a:BotLurk:905749164355379241> No. of Bots :** `{len(list(filter(lambda U : U.bot, GUILD.members)))}` \n" \
                        f"> **<:Reply:930634822865547294> - <a:Users:905749451350638652> Total :** `{GUILD.member_count}` \n",
            inline  =   False)
        USER_EMB.add_field(
            name    =   "<:GeraltRightArrow:904740634982760459> Activity Information :",
            value   =   f"> **<:ReplyContinued:930634770004725821> - <:Online:905757053119766528> Online :** `{USER_STATUS[0]}` \n" \
                        f"> **<:ReplyContinued:930634770004725821> - <:Idle:905757063064453130> Idle :** `{USER_STATUS[1]}` \n" \
                        f"> **<:ReplyContinued:930634770004725821> - <:DnD:905759353141874709> Do Not Disturb :** `{USER_STATUS[2]}` \n" \
                        f"> **<:Reply:930634822865547294> - <:Offline:905757032521551892> Offline :** `{USER_STATUS[3]}`",
            inline  =   False)
        USER_EMB.set_thumbnail(url = GUILD.icon.url)
        USER_EMB.timestamp = disnake.utils.utcnow()
    
        ICON_EMB    =   disnake.Embed(
            title   =   f":scroll: {GUILD.name}'s Icon",
            description =   f"[**JPG Format**]({GUILD.icon.with_static_format('jpg')}) **|** [**PNG Format**]({GUILD.icon.with_static_format('png')}) **|** [**WEBP Format**]({GUILD.icon.with_static_format ('webp')})",
            colour  =   self.bot.colour)
        ICON_EMB.set_image(url = GUILD.icon.url)
        ICON_EMB.timestamp = disnake.utils.utcnow()

        EMBED_LIST  =   [GENERAL_EMB, OTHER_EMB, USER_EMB, ICON_EMB]
        View = Paginator.Paginator(ctx, EMBEDS = EMBED_LIST)
        await ctx.trigger_typing()
        await ctx.reply(embed = EMBED_LIST[0], view = View, allowed_mentions = self.bot.Mention)

    # Taken from R.Danny Bot by Rapptz - Danny [ Github Profile Name ]
    @commands.command(
        name    =   "sql",
        brief   =   "Query DB")
    @commands.is_owner()
    async def sql(self, ctx, *, QUERY : str):
        """Run SQL Queries"""
        QUERY = self.cleanup_code(QUERY)
        
        MULTI_STATE = QUERY.count(";") > 1
        if MULTI_STATE:
            METHOD = self.bot.DB.execute
        else:
            METHOD = self.bot.DB.fetch
        try:
            DB_START    =   time.perf_counter()
            RESULTS     =   await METHOD(QUERY)
            LATENCY     =   (time.perf_counter() - DB_START) * 1000.0
        except Exception:
            return await ctx.message.author.send(f"**<:GeraltRightArrow:904740634982760459> You made a mistake for :**\n```py\n{QUERY}\n```\n```py\n{traceback.format_exc()}\n```")

        ROWS    =   len(RESULTS)
        if MULTI_STATE or ROWS == 0:
            return await ctx.send(f"`{LATENCY:.2f}ms: {RESULTS}`")

        HEADERS =   list(RESULTS[0].keys())
        TABLE   =   CRUCIAL.TabulateData()
        TABLE.columns(HEADERS)
        TABLE.rows_added(list(R.values()) for R in RESULTS)
        RENDERED    =   TABLE.render()

        FINAL = f"{RENDERED}\n"
        if len(FINAL) > 2000:
            await ctx.reply(f"<:ReplyContinued:930634770004725821> - Too much data to send at once...\n<:Reply:930634822865547294> - Returned {CRUCIAL.Plural(ROWS):row} in {LATENCY:.2f}ms", file = disnake.File(io.StringIO(FINAL), filename = "Query-Result.sql"), allowed_mentions = self.bot.Mention)
        else:
            await ctx.reply(f"<:GeraltRightArrow:904740634982760459> Returned {CRUCIAL.Plural(ROWS):row} in {LATENCY:.2f}ms\n```prolog\n{FINAL}\n```", allowed_mentions = self.bot.Mention)

def setup(bot):
    bot.add_cog(Developer(bot))