import io
import typing
import aiohttp
import discord
import traceback
import asyncpg as PSQL

from discord import app_commands
from discord.ext import commands

from bot import CONFIG
import Source.Kernel.Views.Paginator as Paginator
import Source.Kernel.Views.Interface as Interface

class TagFlags(commands.FlagConverter, prefix = "--", delimiter = " ", case_insensitive = True):
    tag : int
    guild : int

class Tags(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Huge thanks to Zeus432 [ Github ID ] for helping me enable the pagination :D
    # Huge thanks to `rtk-rnjn` [ Github ID ] for helping me invoke the tag w/o a separate command

    async def tag_call(self, ctx, tag_name):
        """Call a tag"""
        tag_deets = await self.bot.db.fetchval("SELECT (content) FROM tags WHERE name = $1 AND guild_id = $2", tag_name, ctx.guild.id)
        if not tag_deets:
             return await ctx.reply(f"`{tag_name}` ─ is not present <:SailuShrug:930394489409896448>")
        else:
            await ctx.send(tag_deets, reference = ctx.message.reference if ctx.message.reference else None)
            await self.bot.db.execute("UPDATE tags SET uses = uses + 1 WHERE name = $1 AND author_id = $2 AND guild_id = $3", tag_name, ctx.author.id, ctx.guild.id)

    async def tag_raw(self, ctx, *, tag_name : str = None):
        """Removes all formatting and sends a tag in a raw manner."""
        tag_data = await self.bot.db.fetchval("SELECT (content) FROM tags WHERE name = $1 AND guild_id = $2", tag_name, ctx.guild.id)
        await self.bot.db.execute("UPDATE tags SET uses = uses + 1 WHERE name = $1 AND author_id = $2 AND guild_id = $3", tag_name, ctx.author.id, ctx.guild.id)
        if tag_name is None:
            if ctx.interaction:
                return await ctx.reply(f"**{ctx.author}** ─ call a tag by passing in a `tag_name`", ephemeral = True)
            else:
                return await ctx.reply(f"**{ctx.author}** ─ call a tag by passing in a `tag_name`", ephemeral = False)
        if not tag_data:
            if ctx.interaction:
                return await ctx.reply(f"`{tag_name}` ─ is not present <:SailuShrug:930394489409896448>", ephemeral = True)
            else:
                return await ctx.reply(f"`{tag_name}` ─ is not present <:SailuShrug:930394489409896448>", ephemeral = False)
        else:
            if ctx.interaction:
                await ctx.reply(discord.utils.escape_markdown(tag_data), ephemeral = True)
            else:
                await ctx.reply(discord.utils.escape_markdown(tag_data), ephemeral = False)


    async def tag_list(self, ctx, *, user : typing.Optional[typing.Union[discord.User, discord.Member]]):
        """Get a list of tags made by a user."""
        user = user or ctx.author 
        tag_fetch = await self.bot.db.fetch("SELECT * FROM tags WHERE author_id = $1 AND guild_id = $2 ORDER BY name", user.id, ctx.guild.id)
        tag_list = []
        serial_no = 1
        for tags in tag_fetch:
            tag_list.append(f"> [**{serial_no})**]({tags['jump_url']}) \"**{tags['name']}**\"\n> │ ` ─ ` ID : `{tags['id']}`\n> │ ` ─ ` Uses : `{tags['uses']}`\n> │ ` ─ ` Created : {self.bot.datetime(tags['created_on'], style = 'R')}\n────\n")
            serial_no += 1

        if not tag_fetch:
            if user == ctx.author:
                if ctx.interaction:
                    await ctx.reply(f"**{user}** ─ You own no tags in `{ctx.guild}`. To create one, run `{ctx.clean_prefix}tag make` <:DuckSip:917006564265705482>", ephemeral = True)
                else:
                    await ctx.reply(f"**{user}** ─ You own no tags in `{ctx.guild}`. To create one, run `{ctx.clean_prefix}tag make` <:DuckSip:917006564265705482>", ephemeral = False)
            if user == user:
                if ctx.interaction:
                    await ctx.reply(f"**{user}** ─ owns no tags in `{ctx.guild}`. To create one, run `{ctx.clean_prefix}tag make` <:DuckSip:917006564265705482>", ephemeral = True)
                else:
                    await ctx.reply(f"**{user}** ─ owns no tags in `{ctx.guild}`. To create one, run `{ctx.clean_prefix}tag make` <:DuckSip:917006564265705482>", ephemeral = False)
        else:
            if serial_no <= 4:
                tag_list_emb = discord.Embed(
                    description = f"".join(tasks for tasks in tag_list),
                    colour = self.bot.colour)
                tag_list_emb.set_author(name = f"{user}'s Tag List :")
                tag_list_emb.set_thumbnail(url = user.display_avatar.url)
                tag_list_emb.set_footer(text = f"Run {ctx.clean_prefix}tag for more sub ─ commands.", icon_url = ctx.author.display_avatar)
                tag_list_emb.timestamp = discord.utils.utcnow()
                if ctx.interaction:
                    await ctx.reply(embed = tag_list_emb, mention_author = False, ephemeral = True)
                else:
                    await ctx.reply(embed = tag_list_emb, mention_author = False, ephemeral = False)
            else:
                embed_list = []
                while tag_list:
                    tag_list_emb = discord.Embed(
                        description = "".join(tag_list[:3]),
                        colour = self.bot.colour)
                    tag_list_emb.set_author(name = f"{user}'s Tag List :")
                    tag_list_emb.set_thumbnail(url = user.display_avatar.url)
                    tag_list_emb.set_footer(text = f"Run {ctx.clean_prefix}tag for more sub ─ commands.", icon_url = ctx.author.display_avatar)
                    tag_list_emb.timestamp = discord.utils.utcnow()
                    tag_list = tag_list[3:]
                    embed_list.append(tag_list_emb)     
                await Paginator.Paginator(self.bot, ctx, embeds = embed_list).send(ctx) 

    async def tag_all(self, ctx):
        """Get a list of all tags present in this server."""
        user = ctx.author
        tag_fetch = await self.bot.db.fetch("SELECT * FROM tags WHERE guild_id = $1 ORDER BY name", ctx.guild.id)
        tag_list = []
        serial_no = 1
        for tags in tag_fetch:
            tag_list.append(f"> [**{serial_no})**]({tags['jump_url']}) \"**{tags['name']}**\"\n> │ ` ─ ` Owner : <@{tags['author_id']}>\n> │ ` ─ ` ID : `{tags['id']}` │ Uses : `{tags['uses']}`\n> │ ` ─ ` Created : {self.bot.datetime(tags['created_on'], style = 'R')}\n────\n")
            serial_no += 1

        if not tag_fetch:
            if ctx.interaction:
                await ctx.reply(f"**{user}** ─ There are no tags in `{ctx.guild}`. To create one, run `{ctx.clean_prefix}tag make` and you will get to know <:Okay:913796811737686086>", ephemeral = True)
            else:
                await ctx.reply(f"**{user}** ─ There are no tags in `{ctx.guild}`. To create one, run `{ctx.clean_prefix}tag make` and you will get to know <:Okay:913796811737686086>", ephemeral = False)
        else:
            if serial_no <= 4:
                tag_list_emb = discord.Embed(
                    description = f"".join(tasks for tasks in tag_list),
                    colour = self.bot.colour)
                tag_list_emb.set_author(name = f"{ctx.guild}'s Tag List :")
                tag_list_emb.set_thumbnail(url = ctx.guild.icon.url)
                tag_list_emb.set_footer(text = f"Run {ctx.clean_prefix}tag for more sub ─ commands.", icon_url = ctx.author.display_avatar)
                tag_list_emb.timestamp = discord.utils.utcnow()
                if ctx.interaction:
                    await ctx.reply(embed = tag_list_emb, mention_author = False, ephemeral = True)
                else:
                    await ctx.reply(embed = tag_list_emb, mention_author = False, ephemeral = False)
            else:
                embed_list = []
                while tag_list:
                    tag_list_emb = discord.Embed(
                        title = f"{ctx.guild}'s Tag List :",
                        description = "".join(tag_list[:3]),
                        colour = self.bot.colour)
                    tag_list_emb.set_thumbnail(url = ctx.guild.icon.url)
                    tag_list_emb.set_footer(text = f"Run {ctx.clean_prefix}tag for more sub ─ commands.", icon_url = ctx.author.display_avatar)
                    tag_list_emb.timestamp = discord.utils.utcnow()
                    tag_list = tag_list[3:]
                    embed_list.append(tag_list_emb)     
                await Paginator.Paginator(self.bot, ctx, embeds = embed_list).send(ctx) 
    
    async def tag_info(self, ctx, *, tag_name : commands.clean_content):
        """Get entire details of a tag."""
        tag_deets = await self.bot.db.fetchval("SELECT (id, author_id, content, uses, created_on, jump_url) FROM tags WHERE name = $1 AND guild_id = $2", tag_name, ctx.guild.id)
        if not tag_deets:
            if ctx.interaction:
                return await ctx.reply(f"`{tag_name}` ─ is a tag either which is not present in this guild or not in my database.", ephemeral = True)
            else:
                return await ctx.reply(f"`{tag_name}` ─ is a tag either which is not present in this guild or not in my database.", ephemeral = False)
        tag_owner = await ctx.bot.fetch_user(tag_deets[1])
        jump_button = discord.ui.View()
        jump_button.add_item(discord.ui.Button(label = "Jump to Message", style = discord.ButtonStyle.link, url = tag_deets[5], emoji = "<a:ChainLink:936158619030941706>"))
            
        tag_deets_emb = discord.Embed(
            title = f":scroll: {tag_owner}'s ─ Tag",
            url = tag_deets[5],
            description = f"""The following points showcase full details about the `{tag_name}` tag :
\n────
> │ ` ─ ` Name : \"**{tag_name}**\" (`{tag_deets[0]}`)
> │ ` ─ ` Owner : {tag_owner.mention} (`{tag_owner.id}`)
> │ ` ─ ` Created On : {self.bot.datetime(tag_deets[4], style = 'f')}
> │ ` ─ ` No. of Times Used : `{tag_deets[3]}`
────""",
            colour = self.bot.colour)
        tag_deets_emb.set_thumbnail(url = tag_owner.display_avatar.url)
        tag_deets_emb.timestamp = discord.utils.utcnow()
        if ctx.interaction:
            await ctx.reply(embed = tag_deets_emb, view = jump_button, ephemeral = True)
        else:
            await ctx.reply(embed = tag_deets_emb, view = jump_button, ephemeral = False)

    async def tag_edit(self, ctx, tag_id : int, *, edited_content : str):
        """Edit a tag that you already made"""
        if tag_id != await self.bot.db.fetchval("SELECT * FROM tags WHERE id = $1 AND author_id = $2 AND guild_id = $3", tag_id, ctx.author.id, ctx.guild.id):
            await ctx.reply(f"**{ctx.author}** ─ this is a tag which you either don't own or is not in the database.")
            await ctx.message.add_reaction("<:NanoCross:965845144307912754>")
            return 
        else:
            await self.bot.db.execute("UPDATE tags SET content = $1, author_name = $2 WHERE id = $3 AND author_id = $4 AND guild_id = $5", edited_content, str(ctx.author), tag_id, ctx.author.id, ctx.guild.id)
            tag_deets = await self.bot.db.fetchval("SELECT (name, content) FROM tags WHERE id = $1 AND author_id = $2 AND guild_id = $3", tag_id, ctx.author.id, ctx.guild.id)
                
            class ContentButton(discord.ui.View):

                @discord.ui.button(label = "Edited Content", style = discord.ButtonStyle.grey, emoji = "<a:ZizzyHappy:915131835443474492>")
                async def content_button(self, interaction : discord.Interaction, button : discord.ui.button):
                    await interaction.response.send_message(content = f"Content edited by {ctx.author.mention} :\n\n>>> ────\n{tag_deets[1]}\n────", ephemeral = True)
                    
                async def on_error(self, interaction : discord.Interaction, error : Exception) -> None:
                    async with aiohttp.ClientSession() as session:
                        content_webhook = discord.Webhook.partial(id = CONFIG.get("ERROR_ID"), token = CONFIG.get("ERROR_TOKEN"), session = session)
                    data = "".join(traceback.format_exception(type(error), error, error.__traceback__))
                    try:
                            await content_webhook.send(content = f"```py\n{data}\n```\n|| Break Point ||")
                    except(discord.HTTPException, discord.Forbidden):
                        await content_webhook.send(file = discord.File(io.StringIO(data), filename = "Traceback.py"))
                        await content_webhook.send(content = "|| Break Point ||")
                        await session.close()
                    await interaction.response.send_message(content = f"```py\n{error}\n```", ephemeral = True)

            if ctx.interaction:
                await ctx.reply(f"Successfully edited Tag Name : `{tag_deets[0]}` (`{tag_id}`) ", ephemeral = True)
            else:
                await ctx.reply(f"Successfully edited Tag Name : `{tag_deets[0]}` (`{tag_id}`) ", view = ContentButton(), ephemeral = False)
                await ctx.message.add_reaction("<:NanoTick:925271358735257651>")

    async def tag_remove(self, ctx, id : int):
        """Delete your tag from the server."""
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{ctx.clean_prefix}{ctx.command}` for the `{ctx.command}` command <:SarahPray:920484222421045258>"
        tag_deets = await self.bot.db.fetchval("SELECT (name) FROM tags WHERE id = $1 AND guild_id = $2", id, ctx.guild.id)
        async def yes(ui : discord.ui.View, interaction : discord.Interaction, button : discord.ui.button):
            if interaction.user != ctx.author:
                return interaction.response.send_message(content = f"{pain}", ephemeral = True)
            for view in ui.children:
                view.disabled = True
            if id != await self.bot.db.fetchval("SELECT * FROM tags WHERE id = $1 AND author_id = $2", id, ctx.author.id):
                await interaction.response.defer()
                await ui.response.edit(content = f"\"**{tag_deets}**\" (`{id}`) ─ is a tag which is either not yours or not in the database <a:LifeSucks:932255208044650596>", view = ui)
            else:
                await interaction.response.defer()
                await self.bot.db.execute("DELETE FROM tags WHERE id = $1 AND guild_id = $2 AND author_id = $3", id, ctx.guild.id, ctx.author.id)
                await ui.response.edit(content = f"\"**{tag_deets}**\" (`{id}`) ─ has been successfully deleted from your tag list <:NanoTick:925271358735257651>", view = ui)

        async def no(ui : discord.ui.View, interaction : discord.Interaction, button : discord.ui.button):
            if interaction.user != ctx.author:
                return interaction.response.send_message(content = f"{pain}", ephemeral = True)
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            await ui.response.edit(content = f"\"**{tag_deets}**\" (`{id}`) ─ will not be deleted from your tag list <:NanoTick:925271358735257651>", view = ui)
        
        if ctx.interaction:
            Interface.Confirmation.response = await ctx.reply(f"Are you sure you want to remove tag ─ \"**{tag_deets}**\" (`{id}`) from your list <a:IThink:933315875501641739>", view = Interface.Confirmation(ctx, yes, no), ephemeral = True)    
        else:
            Interface.Confirmation.response = await ctx.reply(f"Are you sure you want to remove tag ─ \"**{tag_deets}**\" (`{id}`) from your list <a:IThink:933315875501641739>", view = Interface.Confirmation(ctx, yes, no), ephemeral = False)    

    async def tag_transfer(self, ctx, tag_id : int, user : discord.Member):
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{ctx.clean_prefix}{ctx.command}` for the `{ctx.command}` command <:SarahPray:920484222421045258>"
        tag_deets = await self.bot.db.fetchval("SELECT (name) FROM tags WHERE id = $1 AND guild_id = $2", tag_id, ctx.guild.id)
        if user is None:
            return await ctx.send(f"Please mention a user to transfer the ownership of the tag.")
        async def yes(ui : discord.ui.View, interaction : discord.Interaction, button : discord.ui.button):
            if interaction.user != ctx.author:
                return interaction.response.send_message(content = f"{pain}", ephemeral = True)
            for view in ui.children:
                view.disabled = True
            if id != await self.bot.db.fetchval("SELECT * FROM tags WHERE id = $1 AND author_id = $2", tag_id, ctx.author.id):
                await interaction.response.defer()
                return await ui.response.edit(content = f"\"**{tag_deets}**\" (`{tag_id}`) ─ is a tag which is either not yours or not in the database <a:LifeSucks:932255208044650596>", view = ui)
            else:
                await interaction.response.defer()
                await self.bot.db.execute("UPDATE tags SET author_id = $1, author_name = $2, author_id = $3 WHERE id = $4 AND guild_id = $5", user.id, user.name, user.id, tag_id, ctx.guild.id)
                await ui.response.edit(content = f"\"**{tag_deets}**\" (`{tag_id}`) ─ has been successfully transferred to {user.mention} <:NanoTick:925271358735257651>", view = ui, allowed_mentions = self.bot.mentions)

        async def no(ui : discord.ui.View, interaction : discord.Interaction, button : discord.ui.button):
            if interaction.user != ctx.author:
                return interaction.response.send_message(content = f"{pain}", ephemeral = True)
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            await ui.response.edit(content = f"\"**{tag_deets}**\" (`{tag_id}`) ─ will not be transfered to {user.mention} <:NanoTick:925271358735257651>", view = ui, allowed_mentions = self.bot.mentions)

        if ctx.interaction:
            Interface.Confirmation.response = await ctx.reply(f"Are you sure you want to \"transfer\" tag ─ \"**{tag_deets}**\" (`{tag_id}`) to {user.mention} <:SIDGoesHmmMan:967421008137056276>", view = Interface.Confirmation(ctx, yes, no), allowed_mentions = self.bot.mentions, ephemeral = True)    
        else:
            Interface.Confirmation.response = await ctx.reply(f"Are you sure you want to \"transfer\" tag ─ \"**{tag_deets}**\" (`{tag_id}`) to {user.mention} <:SIDGoesHmmMan:967421008137056276>", view = Interface.Confirmation(ctx, yes, no), allowed_mentions = self.bot.mentions, ephemeral = False)    

    async def autocomplete(self, interaction : discord.Interaction, current : str) -> typing.List[app_commands.Choice[str]]:
        tag_deets = await self.bot.db.fetch("SELECT (name) FROM tags WHERE guild_id = $1", interaction.guild_id)
        names = [f"{deets[0]}" for deets in tag_deets]
        return [app_commands.Choice(name = names, value = names) for names in names if current.lower() in names]

    async def edit_autocomplete(self, interaction : discord.Interaction, current : int) -> typing.List[app_commands.Choice[int]]:
        tag_deets = await self.bot.db.fetch("SELECT (id) FROM tags WHERE guild_id = $1 AND author_id = $2 ORDER BY id DESC", interaction.guild_id, interaction.user.id)
        ids = [deets[0] for deets in tag_deets]
        return [app_commands.Choice(name = ids, value = ids) for ids in ids]

    @commands.hybrid_group(
        name = "tag",
        brief = "Sub - Commands on tag",
        invoke_without_command = True,
        with_app_command = True)
    @commands.guild_only()
    @app_commands.guild_only()
    async def tag(self, ctx, *, tag_name : str = None):
        """Make me to say something upon being invoking a trigger"""
        if not tag_name:
            return await ctx.send_help(ctx.command)
        if ctx.invoked_subcommand is None:
            await self.tag_call(ctx, tag_name)
            return
    
    @tag.command(
        name = "make",
        brief = "Make a tag",
        aliases = ["add"],
        with_app_command = True)
    async def tag_make(self, ctx):
        f"""Create a tag for `{ctx.guild}`"""
        await Interface.TagButton(self.bot, ctx).send(ctx)

    @tag.command(
        name = "raw",
        brief = "Triggers Tag",
        aliases = ["r"],
        with_app_command = True)
    @app_commands.describe(tag_name = "Choose a tag to view in raw format")
    @app_commands.rename(tag_name = "name")
    @app_commands.autocomplete(tag_name = autocomplete)
    async def _raw(self, ctx, *, tag_name : str):
        await self.tag_raw(ctx, tag_name = tag_name)
    
    @tag.command(
        name = "list",
        brief = "Send user's tags list",
        aliases = ["l"],
        with_app_command = True)    
    @app_commands.describe(user = "Get a list of tags present by the user you mentioned.")
    async def _list(self, ctx, *, user : typing.Optional[typing.Union[discord.User, discord.Member]]):
        await self.tag_list(ctx, user = user)
    
    @tag.command(
        name = "all",
        brief = "Send guild's tags list")
    async def _all(self, ctx):
        await self.tag_all(ctx)
    
    @tag.command(
        name = "info",
        brief = "Get info",
        with_app_command = True)
    @app_commands.autocomplete(tag_name = autocomplete)
    @app_commands.describe(tag_name = "Get information on a tag.")
    @app_commands.rename(tag_name = "name")
    async def _info(self, ctx, *, tag_name : str):
        await self.tag_info(ctx, tag_name = tag_name)

    @tag.command(
        name = "edit",
        brief = "Edit a tag",
        with_app_command = True)
    @app_commands.autocomplete(tag_id = edit_autocomplete)
    @app_commands.describe(tag_id = "ID of the tag you want to edit")
    @app_commands.describe(edited_content = "New content that you want to display upon the tag being called.")
    @app_commands.rename(edited_content = "content")
    @app_commands.rename(tag_id = "id")
    async def _edit(self, ctx, tag_id : int, *, edited_content : str):
        await self.tag_edit(ctx, tag_id = tag_id, edited_content = edited_content)

    @tag.command(
        name = "delete",
        brief = "Remove a Tag",
        aliases = ["remove"],
        with_app_command = True)
    @app_commands.describe(tag_id = "Provide the tag id of which you want to delete.")
    @app_commands.rename(tag_id = "id")
    async def _remove(self, ctx, tag_id : int):
        await self.tag_remove(ctx, id = tag_id)
    
    @tag.command(
        name = "transfer",
        brief = "Transfer Ownership",
        with_app_command = True)
    @app_commands.describe(tag_id = "Provide the ID of the tag you want to transfer to.")
    @app_commands.describe(user = "Mention the user you want to transfer the tag to ")
    @app_commands.rename(tag_id = "id")
    async def _transfer(self, ctx, tag_id : int, *, user : discord.Member):
        await self.tag_transfer(ctx, tag_id = tag_id, user = user)
    
    @tag.command(
        name = "import",
        with_app_command = False)
    async def tag_import(self, ctx, *, flag : typing.Optional[TagFlags]):
        """Import tags from other guilds"""
        if not flag:
            return await ctx.reply("Please pass in `--tag <int>` and `--guild <int>`")
        if flag:
            try:
                tag_deets = await self.bot.db.fetchval("SELECT (name, content) FROM tags WHERE id = $1 AND guild_id = $2", flag.tag, flag.guild)
                insert_query = "INSERT INTO tags (name, content, author_id, author_name, guild_id, created_on, jump_url) VALUES ($1, $2, $3, $4, $5, $6, $7)"
                await self.bot.db.execute(insert_query, tag_deets[0].strip(), tag_deets[1], ctx.author.id, ctx.author.name, ctx.guild.id, ctx.message.created_at, ctx.message.jump_url)
                id = await self.bot.db.fetchval("SELECT (id) FROM tags WHERE guild_id = $1 AND name = $2", ctx.guild.id, tag_deets[0])
                
                class ImportedContent(discord.ui.View):
                    
                    @discord.ui.button(label = "Content", style = discord.ButtonStyle.grey, emoji = "<a:Verify:905748402871095336>")
                    async def imported_tag_content(self, interaction : discord.Interaction, button : discord.ui.Button):
                        await interaction.response.send_message(content = f"{tag_deets[1]}", ephemeral = True)

                await ctx.reply(f"Successfully transferred :\n\n> Tag Name : \"`{tag_deets[0]}`\"\n> Tag ID : `{id}`", view = ImportedContent())
            except PSQL.UniqueViolationError:
                return await ctx.send(f"`{tag_deets[0]}` is a tag which is already present in \"**{ctx.guild}**\"")
            
async def setup(bot):
    await bot.add_cog(Tags(bot))