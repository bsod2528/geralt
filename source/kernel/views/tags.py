import io
import dotenv
import discord
import aiohttp
import traceback
import asyncpg as PSQL

from dotenv import dotenv_values

from ..subclasses.bot import Geralt
from ..subclasses.context import GeraltContext

dotenv.load_dotenv()

CONFIG = dotenv_values("config.env")



# Views for Tags
class TagButton(discord.ui.View):
    def __init__(self, bot : Geralt, ctx : GeraltContext):
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
                    await self.bot.db.execute(f"INSERT INTO tags (name, content, author_id, author_name, guild_id, created_on, jump_url) VALUES ($1, $2, $3, $4, $5, $6, $7)", self.tag_name.value.strip(), self.tag_content.value, self.ctx.author.id, str(self.ctx.author), self.ctx.guild.id, self.ctx.message.created_at, self.ctx.message.jump_url)
                    id = await self.bot.db.fetchval("SELECT id FROM tags WHERE name = $1 AND content = $2", self.tag_name.value, self.tag_content.value)
                    
                    class TagContent(discord.ui.View):
                        def __init__(self, bot, ctx):
                            super().__init__()
                            self.bot = bot
                            self.ctx = ctx

                        @discord.ui.button(label = "Content", style = discord.ButtonStyle.grey, emoji = "<:NanoTick:925271358735257651>")
                        async def on_tag_make_content_view(self, interaction : discord.Interaction, button : discord.ui.Button):
                            try:
                                content = await self.bot.db.fetchval("SELECT content FROM tags WHERE guild_id = $1 AND id = $2 AND author_id = $3", self.ctx.guild.id, id, self.ctx.author.id)
                                await interaction.response.send_message(content = f"\"{content}\"", ephemeral = True)
                            except Exception as exception:
                                await interaction.response.send_message(content = f"```py\n{exception}\n```", ephemeral = True)

                    await interaction.response.send_message(content = f"`{self.tag_name.value}` ─ tag has been created by {interaction.user.mention}. The following points showcase the entire details of the tag :\n\n>>> ────\n` ─ ` Name : \"{self.tag_name.value}\" ─ (`{id}`)\n` ─ ` Created On : {self.bot.timestamp(interaction.created_at, style = 'f')}\n────", ephemeral = False, view = TagContent(self.bot, self.ctx))
            
            except PSQL.UniqueViolationError:
                return await interaction.response.send_message(content = f"`{self.tag_name.value}` ─ is a tag which is already present. Please try again with another with another name", ephemeral = True)
            except Exception as exception:
                return await interaction.response.send_message(content = f"```py\n{exception}\n```", ephemeral = True)
        
        async def on_error(self, interaction : discord.Interaction, error : Exception) -> None:
            async with aiohttp.ClientSession() as session:
                modal_webhook = discord.Webhook.partial(id = CONFIG.get("ERROR_ID"), token = CONFIG.get("ERROR_TOKEN"), session = session)
                data = "".join(traceback.format_exception(type(error), error, error.__traceback__))
                try:
                    await modal_webhook.send(content = f"```py\n{data}\n```\n|| Break Point ||")
                except(discord.HTTPException, discord.Forbidden):
                    await modal_webhook.send(file = discord.File(io.StringIO(data), filename = "Traceback.py"))
                    await modal_webhook.send(content = "|| Break Point ||")
                await session.close()

    @discord.ui.button(label = "Create Tag", style = discord.ButtonStyle.grey, emoji = "<a:PandaNote:961260552435413052>")
    async def create_tag(self, interaction : discord.Interaction, button : discord.ui.Button):
        pain = f"{interaction.user.mention} ─ This view can't be handled by you at the moment <:Bonked:934033408106057738>, it is meant for {self.ctx.author.mention}\nInvoke for youself by running `{self.ctx.clean_prefix}{self.ctx.command}` for the `{self.ctx.command}` command <:SarahPray:920484222421045258>"
        if interaction.user == self.ctx.author:
            button.disabled = True
            await interaction.message.edit(view = self)
            await interaction.response.send_modal(self.ModalTag(self.bot, self.ctx))
        else:
            await interaction.response.send_message(content = f"{pain}", ephemeral = True)        
        
    @discord.ui.button(label = "Help", style = discord.ButtonStyle.grey, emoji = "<a:ReiPet:965800035054931998>")
    async def command_help(self, interaction : discord.Interaction, button : discord.ui.Button):
        
        class TagMakeArgHelpButton(discord.ui.View):
            
            @discord.ui.button(label = "Arguments Taken", style = discord.ButtonStyle.green, emoji = "<a:PandaHappy:915131837158936596>")
            async def arg_button(self, interaction : discord.Interaction, button : discord.ui.button):
                await interaction.response.send_message(content = f"{interaction.user.mention}\n\n>>> ────\n<:GeraltRightArrow:904740634982760459> The following list shows what arguments can be inputted inside the tag :\n │ ` ─ ` Text : Just regular test lol <a:RooSitComfortPatAnotherRoo:916125535015419954>\n │ ` ─ ` Emotes : Emote IDs have to be sent for **custom emotes**. [**Click here to know how to get the custom emote ID**](<https://docs.parent.gg/how-to-obtain-emoji-ids/>). For **default emotes** just do `:<emote>:`\n │ ` ─ ` Codeblocks : A code snippet can be sent by using \`\`\`<language>new line<code>\`\`\` \n │ ` ─ ` Multimedia [ Image & Videos ] : Files which have been sent in discord can be used. Ensure to right click on `video/image` and copy the **link** and paste it.\n────", ephemeral = True)

        await interaction.response.send_message(content = f"{interaction.user.mention}\n\n────\n**Click on the `Arguments Taken` Button for a list of arguments allowed.**\n\nA modal will pop open for you. The following points give a small gist :\n> │ ` ─ ` \"Name\" : Where you're supposed to enter the name of the tag you would like to create.\n> │ ` ─ ` \"Content\" : Where you enter the content for that tag which will be sent upon invoked.\n────\nhttps://i.imgur.com/yAp0dWy.gif", ephemeral = True, view = TagMakeArgHelpButton())

    @discord.ui.button(label = "Exit", style = discord.ButtonStyle.red, emoji = "<a:Byee:915568796536815616>")
    async def exit_tag_creation(self, interaction : discord.Interaction, button : discord.ui.Button):
        pain = f"{interaction.user.mention} ─ This view can't be handled by you at the moment <:Bonked:934033408106057738>, it is meant for {self.ctx.author.mention}\nInvoke for youself by running `{self.ctx.clean_prefix}{self.ctx.command}` for the `{self.ctx.command}` command <:SarahPray:920484222421045258>"
        if interaction.user == self.ctx.author:
            await interaction.response.defer()
            await interaction.delete_original_message()
        else:
            await interaction.response.send_message(content = f"{pain}", ephemeral = True)        

    async def send(self):
        self.message = await self.ctx.send(content = f"**{self.ctx.author}** ─ please utilise the button below to create a new `tag` <a:IWait:948253556190904371>", view = self, ephemeral = False)
        return self.message
        
    async def on_timeout(self) -> None:
        try:
            for view in self.children:
                view.label = "Timed out"
                view.emoji = "<:NanoCross:965845144307912754>"
                view.disabled = True
            return await self.message.edit(content = f"**{self.ctx.author}** ─ I'm sorry to say that this view has timed out <a:VariableCry:942041851228196884>. Please run `{self.ctx.clean_prefix}tag make` to make a tag <a:ZizzyHappy:915131835443474492>", view = self)        
        except Exception:
            pass