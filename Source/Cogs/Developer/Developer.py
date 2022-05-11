import io
import time
import aiohttp
import asyncio
import discord
import textwrap
import humanize
import traceback
import contextlib

from discord.ext import commands
from discord.enums import ButtonStyle

from bot import COGS_EXTENSIONS, CONFIG
import Source.Kernel.Views.Paginator as Paginator
import Source.Kernel.Utilities.Crucial as crucial
import Source.Kernel.Views.Interface as Interface

# Class for buttons in eval command.
class EvalButtons(discord.ui.View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
    
    @discord.ui.button(label = "Traceback", style = ButtonStyle.gray)
    async def traceback(self, interaction : discord.Interaction, button : discord.ui.button):
        tb_emb = discord.Embed(
            title = "Errors Going Boing",
            description = f"{Exception.__class__.__name__} -> {Exception}",
            colour= self.bot.colour)
        await interaction.response.send_message(embed = tb_emb, ephemeral = True)

class Developer(commands.Cog):
    """Developer Commands"""
    def __init__(self, bot):
        self.bot = bot
    
    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])
        return content.strip('` \n')
    
    # Shuts the bot down in a friendly manner.
    @commands.command(
        name = "die",
        brief = "Eternal Sleep",
        aliases = ["snap"])
    @commands.is_owner()
    async def die(self, ctx : commands.Context):
        """Sends the bot to eternal sleep"""
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{ctx.clean_prefix}{ctx.command}` for the `{ctx.command}` command <:SarahPray:920484222421045258>"
        async def yes(ui : discord.ui.View, interaction : discord.Interaction, button : discord.ui.button):
            if interaction.user != ctx.author:
                await interaction.response.send_message(content = f"{pain}", ephemeral = True)
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            await ui.response.edit(content = "Okay then, I shall go to eternal sleep", view = ui, allowed_mentions = self.bot.mentions)
            async with aiohttp.ClientSession() as session:
                death_webhook = discord.Webhook.partial(id = CONFIG.get("NOTIF_ID"), token = CONFIG.get("NOTIF_TOKEN"), session = session)
                await death_webhook.send(content = f"<:GeraltRightArrow:904740634982760459> Going to die right at {self.bot.datetime(discord.utils.utcnow(), style = 'F')} Byee <a:Byee:915568796536815616>\n```prolog\nNo. of Users ─ {len(list(self.bot.get_all_members()))}\nNo. of Guilds ─ {len(self.bot.guilds)}\nDying at ─ {time.strftime('%c', time.gmtime())}```───\n|| Break Point ||")
                await session.close()
            await self.bot.close()

        async def no(ui : discord.ui.View, interaction : discord.Interaction, button : discord.ui.button):
            if interaction.user != ctx.author:
                await interaction.response.send_message(content = f"{pain}", ephemeral = True)
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            await ui.response.edit(content = "Seems like I'm gonna be alive for a bit longer", view = ui, allowed_mentions = self.bot.mentions)
        async with ctx.channel.typing():
            await asyncio.sleep(0.1)
            Interface.Confirmation.response = await ctx.reply("Do you want to kill me?", view = Interface.Confirmation(ctx, yes, no), allowed_mentions = self.bot.mentions)

    @commands.command(
        name = "dm", 
        brief = "dm them")
    async def dm(self, ctx, user : discord.User, *, message : str):
        """DM a particular user."""
        try:
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label = "Support", style = discord.ButtonStyle.link, url = "https://discord.gg/JXEu2AcV5Y", emoji = "<a:BotLurk:905749164355379241>"))
            await user.send(f"<:GeraltRightArrow:904740634982760459> You have received a DM from **BSOD#2528**. If you have any queries, join our support server :\n\n>>> ─────\n{message}\n─────", view = view)
            await ctx.message.add_reaction("<:NanoTick:925271358735257651>")
        except Exception as exception:
            await ctx.send(exception)

    # Evaluate command for running both asynchronous and sychronous programs.
    @commands.command(
        name    =   "eval",
        brief   =   "Run Code",
        aliases =   ["e"])
    @commands.is_owner()
    async def eval(self, ctx : commands.context, *, body : str):
        """Running both asynchronous and sychronous programs"""
        environment = {
            "ctx" : ctx,
            "bot" : self.bot,
            "self" : self,
            "discord" : discord,
            "message" : ctx.message,
            "author" : ctx.author,
            "guild" : ctx.guild,
            "channel" : ctx.channel,
        }

        environment.update(globals())
        if body.startswith( "```" ) and body.endswith( "```" ):
            body = "\n".join(body.split("\n")[1:-1])
        body = body.strip("` \n")
        stdout = io.StringIO()
        compile = f"async def func():\n{textwrap.indent(body, '  ')}"
        try:    
            exec(compile, environment)
        except Exception as exception:
            tb_emb = discord.Embed(
                description = f"```py\n{exception.__class__.__name__} -> {exception}\n```",
                colour = self.bot.colour)
            return await ctx.send(embed = tb_emb)
        func = environment["func"]
        try:
            with contextlib.redirect_stdout(stdout):
                returned_value = await func()
        except Exception as exception:
            value = stdout.getvalue()
            emb = discord.Embed(
                description = f"```py\n{value}{traceback.format_exc()}\n```",
                color = 0x2F3136)
            message = await ctx.send(embed = emb)
            await ctx.message.add_reaction("<:WinUnheck:898572376147623956>")
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction("<:WinCheck:898572324490604605>")
            except:
                pass
            if returned_value is None:
                if value:
                    value_emb = discord.Embed(
                        description = f"```py\n{value}\n```",
                        colour = self.bot.colour)
                    await ctx.send(embed = value_emb, mention_author = False)
            else:
                emb = discord.Embed(
                    description = f"```py\n{value}{returned_value}\n```",
                    colour = self.bot.colour)
                await ctx.send(embed = emb, mention_author = False)

    # Loads extension of choice
    @commands.command(
        name = "load",
        brief = "Loads Cog",
        aliases = ["l"])
    @commands.is_owner()
    async def load(self, ctx : commands.context, *, cog : str):
        """Loads the Extension mentioned."""
        try:
            await self.bot.load_extension(f"Source.Cogs.{cog}")
            async with ctx.channel.typing():
                await asyncio.sleep(0.1)
            await ctx.reply(f"**{cog}** : Successfully Loaded <:RavenPray:914410353155244073>", allowed_mentions = self.bot.mentions)
        except Exception as exception:
            async with ctx.channel.typing():
                await asyncio.sleep(0.1)
            await ctx.reply(f"Couldn't load **{cog}** : `{exception}`", allowed_mentions = self.bot.mentions)

    # Unloads extension of choice
    @commands.command(
        name = "unload",
        brief = "Unloads Cog",
        aliases = ["ul"])
    @commands.is_owner()
    async def unload(self, ctx : commands.context, *, cog : str):
        """Unloads the Extension mentioned."""
        try:
            await self.bot.unload_extension(f"Source.Cogs.{cog}")
            async with ctx.channel.typing():
                await asyncio.sleep(0.1)
            await ctx.reply(f"**{cog}** : Successfully Unloaded <:RavenPray:914410353155244073>", allowed_mentions = self.bot.mentions)
        except Exception as exception:
            async with ctx.channel.typing():
                await asyncio.sleep(0.1)
            await ctx.reply(f"Couldn't unload **{cog}** : `{exception}`", allowed_mentions = self.bot.mentions)
 
    # Reloads extension of choice
    @commands.command(
        name = "reload",
        brief = "Reloads Cog",
        aliases = ["rl"])
    @commands.is_owner()
    async def reload(self, ctx : commands.context, *, cog : str = None):
        """Reloads the Extension mentioned."""
        if cog is None:
            try:
                for cogs in COGS_EXTENSIONS:
                    await self.bot.reload_extension(cogs)
                await ctx.reply(f"Reloaded `{len(cogs)}` files <:RavenPray:914410353155244073>")
            except Exception as exception:
                async with ctx.channel.typing():
                    await asyncio.sleep(0.1)
                    await ctx.reply(f"Couldn't reload all the extensions : `{exception}`", allowed_mentions = self.bot.mentions)
        else:
            try:
                await self.bot.reload_extension(f"Source.Cogs.{cog}")
                async with ctx.channel.typing():
                    await asyncio.sleep(0.1)
                await ctx.reply(f"**{cog}** : Successfully Reloaded <:RavenPray:914410353155244073>", allowed_mentions = self.bot.mentions)
            except Exception as exception:
                async with ctx.channel.typing():
                    await asyncio.sleep(0.1)
                    await ctx.reply(f"Couldn't reload **{cog}** : `{exception}`", allowed_mentions = self.bot.mentions)
  
    # Group of Commands used for changing presence.
    @commands.group(
        name = "dev",
        brief = "Simple Dev Stuff",
        aliases = ["devmode"])
    @commands.is_owner()
    async def dev(self, ctx):
        """Simple commands for dev to do"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @dev.command(
        name  = "total-guilds",
        aliases = ["tg"],
        brief = "Sends Guild List")
    async def total_guilds(self, ctx):
        """Sends the entire guild list."""
        await ctx.reply(f"Currently in `{len(self.bot.guilds)}` Guilds.", allowed_mentions = self.bot.mentions)
        await ctx.send(f" ".join([f"> │ ` ─ ` \"{g.name}\" : {g.owner.mention} (`{g.id}`)\n" for g in self.bot.guilds]) + "", allowed_mentions = self.bot.mentions)
  
    @dev.command(
        name = "on",
        brief = "Sets Status Offline")
    async def on(self, ctx):
        """Sets the bot status as Invisible"""
        await self.bot.change_presence(
            status = discord.Status.invisible)
        await ctx.message.add_reaction("<:Offline:905757032521551892>")

    @dev.command(
        name = "off",
        brief = "Sets Status Idle")
    async def off(self, ctx):
        """Sets the bot status as Idle"""
        await self.bot.change_presence(
            status = discord.Status.idle,
            activity = discord.Activity(type = discord.ActivityType.listening, name = ".ghelp"))
        await ctx.message.add_reaction("<:Idle:905757063064453130>")
  
    @dev.command(
        name = "leave",
        brief = "Leaves Guild")
    async def off(self, ctx, *, guild : int):
        """Sets the bot status as Idle"""
        guild = await self.bot.fetch_guild(guild)
        await guild.leave()
        await ctx.reply(f"Left **{guild}** on {self.bot.datetime(discord.utils.utcnow(), style = 'F')}")
  
    @commands.command(
        name = "guildfetch",
        brief = "Get guild information",
        aliases = ["fg"])
    @commands.is_owner()
    async def guild_fetch(self, ctx : commands.context, *, guild : discord.Guild):
        """Get entire details about the guild."""
        fetched_guild = await ctx.bot.fetch_guild(guild.id)
        user_status = [
                        len(list(filter(lambda u : str(u.status) == "online", guild.members))),
                        len(list(filter(lambda u : str(u.status) == "idle", guild.members))),
                        len(list(filter(lambda u : str(u.status) == "dnd", guild.members))),
                        len(list(filter(lambda u : str(u.status) == "offline", guild.members)))
                      ]
        
        general_emb = discord.Embed(
            title = f":scroll: {guild.name}'s Information",
            colour = self.bot.colour)
        general_emb.add_field(
            name = "<:GeraltRightArrow:904740634982760459> General Information :",
            value = f"> **<:ReplyContinued:930634770004725821> - <a:Owner:905750348457738291> Owner :** {guild.owner.mention} (`{guild.owner.id}`) \n" \
                    f"> **<:ReplyContinued:930634770004725821> - <a:Users:905749451350638652> No. of Roles :** `{len(guild.roles)}` \n" \
                    f"> **<:ReplyContinued:930634770004725821> - <a:Info:905750331789561856> Identification No. :** `{guild.id}` \n" \
                    f"> **<:ReplyContinued:930634770004725821> - <a:Verify:905748402871095336> Verification Level :** {str(guild.verification_level).replace('_', ' ').replace('`None`', '`Nill`').title()} \n" \
                    f"> **<:Reply:930634822865547294> - <:WinFileBruh:898571301986373692> File Transfer Limit:** `{humanize.naturalsize(guild.filesize_limit)}`")
        general_emb.add_field(
            name = "<:GeraltRightArrow:904740634982760459> Initialisation :",
            value = f"> **<:ReplyContinued:930634770004725821> - <a:Woo:905754435379163176> Made On :** {self.bot.datetime(guild.created_at)} \n" \
                    f"> **<:Reply:930634822865547294> - <:ISus:915817563307515924> Media Filteration :** For `{str(guild.explicit_content_filter).replace('_',' ').replace('`None`', '`Nill`').title()}` \n",
            inline = False)
        general_emb.set_thumbnail(url = guild.icon.url)
        general_emb.timestamp = discord.utils.utcnow()

        other_emb = discord.Embed(
            title = f":scroll: {guild.name}'s Other Information",
            colour = self.bot.colour)
        other_emb.add_field(
            name = "<:GeraltRightArrow:904740634982760459> Channel Information :",
            value = f"> **<:ReplyContinued:930634770004725821> - <:Channel:905674680436944906> Text :** `{len(guild.text_channels)}` \n" \
                    f"> **<:ReplyContinued:930634770004725821> - <:Voice:905746719034187796> Voice :** `{len(guild.voice_channels)}` \n" \
                    f"> **<:ReplyContinued:930634770004725821> - <a:Thread:905750997706629130> Threads :** `{len(guild.threads)}` \n" \
                    f"> **<:Reply:930634822865547294> - <:StageChannel:905674422839554108> Stage :** `{len(guild.stage_channels)}` \n",
            inline = False)
        other_emb.add_field(
            name = "<:GeraltRightArrow:904740634982760459> Emotes Present :",
            value = f"> **<:ReplyContinued:930634770004725821> - <a:IThink:933315875501641739> Animated :** `{len([animated for animated in guild.emojis if animated.animated])}` / `{guild.emoji_limit}` \n" \
                    f"> **<:Reply:930634822865547294> - <:BallManHmm:933398958263386222> Non - Animated :** `{len([non_animated for non_animated in guild.emojis if not non_animated.animated])}` / `{guild.emoji_limit}`",
            inline = False)
        other_emb.set_thumbnail(url = guild.icon.url)
        other_emb.timestamp = discord.utils.utcnow()

        user_emb = discord.Embed(
            title = f":scroll: {guild.name}'s Users Information",
            colour = self.bot.colour)
        user_emb.add_field(
            name = "<:GeraltRightArrow:904740634982760459> No. of User :",
            value = f"> **<:ReplyContinued:930634770004725821> - <a:HumanBro:905748764432662549> No. of Humans :** `{len(list(filter(lambda U : U.bot is False, guild.members)))}` \n" \
                    f"> **<:ReplyContinued:930634770004725821> - <a:BotLurk:905749164355379241> No. of Bots :** `{len(list(filter(lambda U : U.bot, guild.members)))}` \n" \
                    f"> **<:Reply:930634822865547294> - <a:Users:905749451350638652> Total :** `{guild.member_count}` \n",
            inline = False)
        user_emb.add_field(
            name = "<:GeraltRightArrow:904740634982760459> Activity Information :",
            value = f"> **<:ReplyContinued:930634770004725821> - <:Online:905757053119766528> Online :** `{user_status[0]}` \n" \
                    f"> **<:ReplyContinued:930634770004725821> - <:Idle:905757063064453130> Idle :** `{user_status[1]}` \n" \
                    f"> **<:ReplyContinued:930634770004725821> - <:DnD:905759353141874709> Do Not Disturb :** `{user_status[2]}` \n" \
                    f"> **<:Reply:930634822865547294> - <:Offline:905757032521551892> Offline :** `{user_status[3]}`",
            inline = False)
        user_emb.set_thumbnail(url = guild.icon.url)
        user_emb.timestamp = discord.utils.utcnow()
    
        icon_emb = discord.Embed(
            title = f":scroll: {guild.name}'s Icon",
            description = f"[**JPG Format**]({guild.icon.with_static_format('jpg')}) **|** [**PNG Format**]({guild.icon.with_static_format('png')}) **|** [**WEBP Format**]({guild.icon.with_static_format ('webp')})",
            colour = self.bot.colour)
        icon_emb.set_image(url = guild.icon.url)
        icon_emb.timestamp = discord.utils.utcnow()

        banner_emb = None

        if fetched_guild.banner is None:
            embed_list = [general_emb, other_emb, user_emb, icon_emb]
            async with ctx.channel.typing():
                await asyncio.sleep(0.1)
            await Paginator.Paginator(self.bot, ctx, embeds = embed_list).send(ctx)
        else:
            banner_emb = discord.Embed(
                title = f":scroll: {guild.name}'s Banner",
                description = f"[**Download Banner Here**]({fetched_guild.banner.url})",
                colour = self.bot.colour)
            banner_emb.set_image(url = fetched_guild.banner.url)
            banner_emb.timestamp = discord.utils.utcnow()
            
            embed_list = [general_emb, other_emb, user_emb, icon_emb, banner_emb]
            async with ctx.channel.typing():
                await asyncio.sleep(0.1)
            await Paginator.Paginator(self.bot, ctx, embeds = embed_list).send(ctx)
  
    # Taken from R.Danny Bot by Rapptz - Danny [ Github Profile Name ]
    @commands.command(
        name = "sql",
        brief = "Query DB")
    @commands.is_owner()
    async def sql(self, ctx : commands.context, *, query : str):
        """Run SQL Queries"""
        query = self.cleanup_code(query)
        
        multi_line = query.count(";") > 1
        if multi_line:
            method = self.bot.db.execute
        else:
            method = self.bot.db.fetch
        try:
            db_start = time.perf_counter()
            results = await method(query)
            latency = (time.perf_counter() - db_start) * 1000.0
        except Exception:
            return await ctx.reply(f"```py\n{traceback.format_exc()}\n```", mention_author = False)

        rows = len(results)
        if multi_line or rows == 0:
            return await ctx.send(f"`{latency:.2f}ms: {results}`")

        headers = list(results[0].keys())
        table = crucial.TabulateData()
        table.columns(headers)
        table.rows_added(list(r.values()) for r in results)
        rendered = table.render()

        final = f"{rendered}\n"
        async with ctx.channel.typing():
            await asyncio.sleep(0.1)
        await ctx.reply(f"<:GeraltRightArrow:904740634982760459> Returned {crucial.Plural(rows):row} in {latency:.2f}ms", file = discord.File(io.StringIO(final), filename = "Query-Result.sql"), allowed_mentions = self.bot.mentions)
      
async def setup(bot):
    await bot.add_cog(Developer(bot))