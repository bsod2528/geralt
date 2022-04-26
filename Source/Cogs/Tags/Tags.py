import io
import aiohttp
import discord
import traceback
import asyncpg as PSQL

from discord.ext import commands

from bot import CONFIG
import Source.Kernel.Views.Paginator as Paginator
import Source.Kernel.Views.Interface as Interface

class ButtonTag(discord.ui.View):
    def __init__(self, bot, ctx):
        super().__init__(timeout = 100)
        self.bot = bot
        self.ctx = ctx

    class ModalTag(discord.ui.Modal, title = "Create a Tag !"):
        def __init__(self, bot, ctx):
            super().__init__()
            self.bot = bot
            self.ctx = ctx

        tag_name = discord.ui.TextInput(
            label = "Name",
            placeholder = "Please enter the name of the tag.")
    
        tag_content = discord.ui.TextInput(
            label = "Content",
            style = discord.TextStyle.paragraph,
            required = True, 
            placeholder = "Enter the content of the tag.")
    
        async def on_submit(self, interaction : discord.Interaction) -> None:
            try:
                blacklisted_words = ["make", "raw", "info", "transfer", "delete", "edit", "list", "all"]
                if self.tag_name.value.strip() in blacklisted_words:
                    return await interaction.response.send_message(content = f"{interaction.user.mention} ─ `make` is a reserved keyword. Please try again using another word", ephemeral = True)
                else:
                    await self.bot.db.execute(f"INSERT INTO tags (name, content, author_id, author_name, guild_id, created_on, jump_url) VALUES ($1, $2, $3, $4, $5, $6, $7)", self.tag_name.value.strip(), self.tag_content.value, self.ctx.author.id, self.ctx.author.name, self.ctx.guild.id, self.ctx.message.created_at, self.ctx.message.jump_url)
                    id = await self.bot.db.fetchval("SELECT id FROM tags WHERE name = $1 AND content = $2", self.tag_name.value, self.tag_content.value)
                    await interaction.user.send(content = f"The following has been stored in the database :\n\n>>> ────\n` ─ ` ID : \"{id}\"\n` ─ ` Name : \"{self.tag_name.value}\"\n` ─ ` Content : \"{self.tag_content.value}\"\n────")
                    await interaction.response.send_message(content = f"`{self.tag_name.value}` ─ tag has been created by {interaction.user.mention}. The following points showcase the entire details of the tag :\n\n>>> ────\n` ─ ` Name : \"{self.tag_name.value}\" ─ (`{id}`)\n` ─ ` Content : \n\"{self.tag_content.value}\"\n` ─ ` Created On : {self.bot.datetime(interaction.created_at, style = 'f')}\n────", ephemeral = False)
            
            except PSQL.UniqueViolationError:
                return await interaction.response.send_message(content = f"`{self.tag_name.value}` ─ is a tag which is already present. Please try again with another with another name", ephemeral = True)
            except Exception as exception:
                return await interaction.response.send_message(content = f"```py\n{exception}\n```", ephemeral = True)
        
        async def on_error(self, error : Exception, interaction : discord.Interaction) -> None:
            async with aiohttp.ClientSession() as session:
                modal_webhook = discord.Webhook.partial(id = CONFIG.get("ERROR_ID"), token = CONFIG.get("ERROR_TOKEN"), session = session)
                data = "".join(traceback.format_exception(type(error), error, error.__traceback__))
                try:
                    await modal_webhook.send(content = f"```py\n{data}\n```\n|| Break Point ||")
                except(discord.HTTPException, discord.Forbidden):
                    await modal_webhook.send(file = discord.File(io.StringIO(data), filename = "Traceback.py"))
                    await modal_webhook.send(content = "|| Break Point ||")
                await session.close()

    @discord.ui.button(label = "Create Tag", style = discord.ButtonStyle.grey, emoji = "<a:Verify:905748402871095336>")
    async def create_tag(self, interaction : discord.Interaction, button : discord.ui.button):
        pain = f"{interaction.user.mention} ─ This view can't be handled by you at the moment <:Bonked:934033408106057738>, it is meant for {self.ctx.author.mention}\nInvoke for youself by running `{self.ctx.clean_prefix}{self.ctx.command}` for the `{self.ctx.command}` command <:SarahPray:920484222421045258>"
        if interaction.user == self.ctx.author:
            button.disabled = True
            await interaction.message.edit(view = self)
            await interaction.response.send_modal(self.ModalTag(self.bot, self.ctx))
        else:
            await interaction.response.send_message(content = f"{pain}", ephemeral = True)        
        
    @discord.ui.button(label = "Help", style = discord.ButtonStyle.grey, emoji = "<a:ReiPet:965800035054931998>")
    async def command_help(self, interaction : discord.Interaction, button : discord.ui.button):
        
        class TagMakeArgHelpButton(discord.ui.View):
            
            @discord.ui.button(label = "Arguments Taken", style = discord.ButtonStyle.green, emoji = "<a:PandaHappy:915131837158936596>")
            async def arg_button(self, interaction : discord.Interaction, button : discord.ui.button):
                await interaction.response.send_message(content = f"{interaction.user.mention}\n\n>>> ────\n<:GeraltRightArrow:904740634982760459> The following list shows what arguments can be inputted inside the tag :\n │ ` ─ ` Text : Just regular test lol <a:RooSitComfortPatAnotherRoo:916125535015419954>\n │ ` ─ ` Emotes : Emote IDs have to be sent for **custom emotes**. [**Click here to know how to get the custom emote ID**](<https://docs.parent.gg/how-to-obtain-emoji-ids/>). For **default emotes** just do `:<emote>:`\n │ ` ─ ` Codeblocks : A code snippet can be sent by using \`\`\`<language>new line<code>\`\`\` \n │ ` ─ ` Multimedia [ Image & Videos ] : Files which have been sent in discord can be used. Ensure to right click on `video/image` and copy the **link** and paste it.\n────", ephemeral = True)

        await interaction.response.send_message(content = f"{interaction.user.mention}\n\n────\n**Click on the `Arguments Taken` Button for a list of arguments allowed.**\n\nA modal will pop open for you. The following points give a small gist :\n> │ ` ─ ` \"Name\" : Where you're supposed to enter the name of the tag you would like to create.\n> │ ` ─ ` \"Content\" : Where you enter the content for that tag which will be sent upon invoked.\n────\nhttps://i.imgur.com/yAp0dWy.gif", ephemeral = True, view = TagMakeArgHelpButton())
        
    async def send(self, ctx):
        self.message = await ctx.send(content = f"**{ctx.author}** ─ please utilise the button below to create a new `tag` <a:IWait:948253556190904371>", view = self)
        return self.message
        
    async def on_timeout(self) -> None:
        try:
            for view in self.children:
                view.label = "Timed out"
                view.emoji = "<:NanoCross:965845144307912754>"
                view.disabled = True
            return await self.message.edit(content = f"**{self.ctx.author}** ─ I'm sorry to say that this view has timed out <a:VariableCry:942041851228196884>. Please run `{self.ctx.clean_prefix}tag make` to make a tag <a:ZizzyHappy:915131835443474492>", view = self)        
        except Exception:
            return

class Tags(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Huge thanks to `rtk-rnjn` [ Github ID ] for helping me invoke the tag w/o a separate command
    @commands.group(
        name = "tag",
        brief = "Sub - Commands on tag",
        invoke_without_command = True)
    @commands.guild_only()
    async def tag(self, ctx, *, tag_name : str = None):
        """Make me to say something upon being invoking a trigger"""
        if not tag_name:
            return await ctx.send_help(ctx.command)
        if ctx.invoked_subcommand is None:
            await self.show_tag(ctx, tag_name)
            return

    async def show_tag(self, ctx, tag_name):
        tag_deets = await self.bot.db.fetchval("SELECT (content) FROM tags WHERE name = $1 AND guild_id = $2", tag_name, ctx.guild.id)
        if not tag_deets:
             return await ctx.reply(f"`{tag_name}` ─ is not present <:SailuShrug:930394489409896448>")
        else:
             await ctx.send(tag_deets, reference = ctx.message.reference if ctx.message.reference else None)
             await self.bot.db.execute("UPDATE tags SET uses = uses + 1 WHERE name = $1 AND author_id = $2 AND guild_id = $3", tag_name, ctx.author.id, ctx.guild.id)

    @tag.command(
        name = "make",
        brief = "Make a tag",
        aliases = ["add"])
    async def tag_make(self, ctx):
        f"""Create a tag for `{ctx.guild}`"""
        await ButtonTag(self.bot, ctx).send(ctx)

    @tag.command(
        name = "raw",
        brief = "Triggers Tag",
        aliases = ["r"])
    async def tag_raw(self, ctx, *, tag_name : str = None):
        tag_data = await self.bot.db.fetchval("SELECT (content) FROM tags WHERE name = $1 AND guild_id = $2", tag_name, ctx.guild.id)
        await self.bot.db.execute("UPDATE tags SET uses = uses + 1 WHERE name = $1 AND author_id = $2 AND guild_id = $3", tag_name, ctx.author.id, ctx.guild.id)
        if tag_name is None:
            return await ctx.reply(f"**{ctx.author}** ─ call a tag by passing in a `tag_name`")
        if not tag_data:
            return await ctx.send(f"`{tag_name}` ─ is not present <:SailuShrug:930394489409896448>")
        else:
            await ctx.send(discord.utils.escape_markdown(tag_data))

    @tag.command(
        name = "list",
        brief = "Send tags list",
        aliases = ["l"])
    async def tag_list(self, ctx, flag : str):
        user = ctx.author
        tag_fetch = await self.bot.db.fetch("SELECT * FROM tags WHERE author_id = $1 AND guild_id = $2", ctx.author.id, ctx.guild.id)
        tag_list = []
        serial_no = 1
        for tags in tag_fetch:
            tag_list.append(f"> [**{serial_no})**]({tags['jump_url']}) \"**{tags['name']}**\"\n> │ ` ─ ` ID : {tags['id']}\n> │ ` ─ ` Created : {self.bot.datetime(tags['created_on'], style = 'R')}\n────\n")
            serial_no += 1

        if not tag_fetch:
            await ctx.reply(f"**{user}** ─ You own no tags in `{ctx.guild}`. To create one, run `{ctx.clean_prefix}tag` and you will get to know <:Okay:913796811737686086>")
        else:
            if serial_no <= 4:
                tag_list_emb = discord.Embed(
                    description = f"".join(tasks for tasks in tag_list),
                    colour = self.bot.colour)
                tag_list_emb.set_author(name = f"{ctx.author}'s Tag List :")
                tag_list_emb.set_thumbnail(url = ctx.author.display_avatar.url)
                tag_list_emb.set_footer(text = f"Run {ctx.clean_prefix}tag for more sub ─ commands.")
                tag_list_emb.timestamp = discord.utils.utcnow()
                await ctx.reply(embed = tag_list_emb, mention_author = False)
            else:
                # Huge thanks to Zeus432 [ Github ID ] for helping me enable the pagination :D
                embed_list = []
                while tag_list:
                    tag_list_emb = discord.Embed(
                        description = "".join(tag_list[:3]),
                        colour = self.bot.colour)
                    tag_list_emb.set_author(name = f"{ctx.author}'s Tag List :")
                    tag_list_emb.set_thumbnail(url = ctx.author.display_avatar.url)
                    tag_list_emb.set_footer(text = f"Run {ctx.clean_prefix}tag for more sub ─ commands.")
                    tag_list_emb.timestamp = discord.utils.utcnow()
                    tag_list = tag_list[3:]
                    embed_list.append(tag_list_emb)     
                await Paginator.Paginator(self.bot, ctx, embeds = embed_list).send(ctx) 
    
    @tag.command(
        name = "all",
        brief = "Send tags list")
    async def tag_all(self, ctx):
        user = ctx.author
        tag_fetch = await self.bot.db.fetch("SELECT * FROM tags WHERE guild_id = $1", ctx.guild.id)
        tag_list = []
        serial_no = 1
        for tags in tag_fetch:
            tag_list.append(f"> [**{serial_no})**]({tags['jump_url']}) \"**{tags['name']}**\" ─ ID : `{tags['id']}`│ Uses : `{tags['uses']}`\n> │ ` ─ ` Owner : <@{tags['author_id']}>\n> │ ` ─ ` Created : {self.bot.datetime(tags['created_on'], style = 'R')}\n────\n")
            serial_no += 1

        if not tag_fetch:
            await ctx.reply(f"**{user}** ─ There are no tags in `{ctx.guild}`. To create one, run `{ctx.clean_prefix}tag` and you will get to know <:Okay:913796811737686086>")
        else:
            if serial_no <= 5:
                tag_list_emb = discord.Embed(
                    description = f"".join(tasks for tasks in tag_list),
                    colour = self.bot.colour)
                tag_list_emb.set_author(name = f"{ctx.guild}'s Tag List :")
                tag_list_emb.set_thumbnail(url = ctx.guild.icon.url)
                tag_list_emb.set_footer(text = f"Run {ctx.clean_prefix}tag for more sub ─ commands.")
                tag_list_emb.timestamp = discord.utils.utcnow()
                await ctx.reply(embed = tag_list_emb, mention_author = False)
            else:
                # Huge thanks to Zeus432 [ Github ID ] for helping me enable the pagination :D
                embed_list = []
                while tag_list:
                    tag_list_emb = discord.Embed(
                        title = f"{ctx.guild}'s Tag List :",
                        description = "".join(tag_list[:5]),
                        colour = self.bot.colour)
                    tag_list_emb.set_thumbnail(url = ctx.guild.icon.url)
                    tag_list_emb.set_footer(text = f"Run {ctx.clean_prefix}tag for more sub ─ commands.")
                    tag_list_emb.timestamp = discord.utils.utcnow()
                    tag_list = tag_list[5:]
                    embed_list.append(tag_list_emb)     
                await Paginator.Paginator(self.bot, ctx, embeds = embed_list).send(ctx) 
    @tag.command(
        name = "info",
        brief = "Get info")
    async def tag_info(self, ctx, *, tag_name : commands.clean_content):
        try:
            tag_deets = await self.bot.db.fetchval("SELECT (id, author_id, content, uses, created_on, jump_url) FROM tags WHERE name = $1 AND guild_id = $2", tag_name, ctx.guild.id)
            if not tag_deets:
                return await ctx.reply(f"`{tag_name}` ─ is a tag either which is not present in this guild or not in my database.")
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
> │ ` ─ ` No. of Times Used : ` {tag_deets[3]} `
────""",
                colour = self.bot.colour)
            tag_deets_emb.set_thumbnail(url = tag_owner.display_avatar.url)
            tag_deets_emb.timestamp = discord.utils.utcnow()
            await ctx.send(embed = tag_deets_emb, view = jump_button)
        except Exception as exception:
            await ctx.send(exception)

    @tag.command(
        name = "edit",
        brief = "Edit a tag")
    async def tag_edit(self, ctx, tag_id : int, *, edited_content : str):
        """Edit a tag that you already made"""
        if tag_id != await self.bot.db.fetchval("SELECT * FROM tags WHERE id = $1 AND author_id = $2 AND guild_id = $3", tag_id, ctx.author.id, ctx.guild.id):
            await ctx.reply(f"**{ctx.author}** ─     this is a tag which you either don't own or is not in the database.")
            await ctx.message.add_reaction("<:NanoCross:965845144307912754>")
            return 
        else:
            try:
                await self.bot.db.execute("UPDATE tags SET content = $1 WHERE id = $2 AND author_id = $3 AND guild_id = $4", edited_content, tag_id, ctx.author.id, ctx.guild.id)
                tag_deets = await self.bot.db.fetchval("SELECT (name, content) FROM tags WHERE id = $1 AND author_id = $2 AND guild_id = $3", tag_id, ctx.author.id, ctx.guild.id)
                await ctx.reply(f"""Successfully edited Tag Name : `{tag_deets[0]}` (`{tag_id}`) with the following details :
\n────
> │ ` ─ ` Content : \"{tag_deets[1]}\"
> │ ` ─ ` Edited On : {self.bot.datetime(ctx.message.created_at, style = 'f')}
────""")
                await ctx.message.add_reaction("<:NanoTick:925271358735257651>")
            except Exception as exception:
                await ctx.send(f"{exception}")
                await ctx.message.add_reaction("<:NanoCross:965845144307912754>")

    @tag.command(
        name = "delete",
        brief = "Remove a Tag",
        aliases = ["remove"])
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
                return await ui.response.edit(f"\"**{tag_deets}**\" (`{id}`) ─ is a tag which is either not yours or not in the database <a:LifeSucks:932255208044650596>", view = ui)
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

        Interface.Confirmation.response = await ctx.reply(f"Are you sure you want to remove tag ─ \"**{tag_deets}**\" (`{id}`) from your list <a:IThink:933315875501641739>", view = Interface.Confirmation(ctx, yes, no))    

    @tag.command(
        name = "transfer",
        brief = "Transfer Ownership")
    async def tag_transfer(self, ctx, id : int, user : discord.Member = None):
        pain = f"This view can't be handled by you at the moment, invoke for youself by running `{ctx.clean_prefix}{ctx.command}` for the `{ctx.command}` command <:SarahPray:920484222421045258>"
        tag_deets = await self.bot.db.fetchval("SELECT (name) FROM tags WHERE id = $1 AND guild_id = $2", id, ctx.guild.id)
        if user is None:
            return await ctx.send(f"Please mention a user to transfer the ownership of the tag.")
        async def yes(ui : discord.ui.View, interaction : discord.Interaction, button : discord.ui.button):
            if interaction.user != ctx.author:
                return interaction.response.send_message(content = f"{pain}", ephemeral = True)
            for view in ui.children:
                view.disabled = True
            if id != await self.bot.db.fetchval("SELECT * FROM tags WHERE id = $1 AND author_id = $2", id, ctx.author.id):
                await interaction.response.defer()
                return await ui.response.edit(f"\"**{tag_deets}**\" (`{id}`) ─ is a tag which is either not yours or not in the database <a:LifeSucks:932255208044650596>", view = ui)
            else:
                await interaction.response.defer()
                await self.bot.db.execute("UPDATE tags SET author_id = $1, author_name = $2 WHERE id = $3 AND guild_id = $4", user.id, user.name, id, ctx.guild.id)
                await ui.response.edit(content = f"\"**{tag_deets}**\" (`{id}`) ─ has been successfully transferred to {user.mention} <:NanoTick:925271358735257651>", view = ui, allowed_mentions = self.bot.mentions)

        async def no(ui : discord.ui.View, interaction : discord.Interaction, button : discord.ui.button):
            if interaction.user != ctx.author:
                return interaction.response.send_message(content = f"{pain}", ephemeral = True)
            for view in ui.children:
                view.disabled = True
            await interaction.response.defer()
            await ui.response.edit(content = f"\"**{tag_deets}**\" (`{id}`) ─ will not be transfered to {user.mention} <:NanoTick:925271358735257651>", view = ui, allowed_mentions = self.bot.mentions)

        Interface.Confirmation.response = await ctx.reply(f"Are you sure you want to \"transfer\" tag ─ \"**{tag_deets}**\" (`{id}`) to {user.mention} <:SIDGoesHmmMan:967421008137056276>", view = Interface.Confirmation(ctx, yes, no), allowed_mentions = self.bot.mentions)    
    
async def setup(bot):
    await bot.add_cog(Tags(bot))