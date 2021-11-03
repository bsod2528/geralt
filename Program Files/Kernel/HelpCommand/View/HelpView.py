import discord
import datetime
from discord.components import Button
from discord.enums import ButtonStyle
from discord.ext import commands
from discord.ext.commands.core import check

class HelpMenuUI(discord.ui.Select):
    def __init__(self, view, **kwargs):
        super().__init__(**kwargs)
        self.help = view.help
        self.mapping = view.mapping
        self.main = view.main
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)
        self.color =  0x2F3136

    def gts(self, command):
        return f'<:GeraltRightArrow:904740634982760459> `{command.qualified_name}` - {command.brief}\n'

    async def callback(self, interaction:discord.Interaction):
        for cog, commands in self.mapping.items():
            name = f'{cog.qualified_name}' if cog else 'Essential'
            description = f'{cog.description}' if cog else 'Commands without category'
            cmds = cog.walk_commands() if cog else commands
            if self.values[0] == name:
                emb = discord.Embed(
                    color = self.color,
                    title = f'{self.help.emojis.get(name) if self.help.emojis.get(name) else None} {name}',
                    description = f"{description}\n\n{''.join(self.gts(command) for command in cmds)}",
                    timestamp = self.timestamp
                )
                emb.set_footer(
                    text = '')
                await interaction.response.edit_message(embed = emb)
                
class HelpMenu(discord.ui.View):
    def __init__(self, help, mapping):
        super().__init__(timeout = 60)
        self.help = help
        self.mapping = mapping
        self.color = 0x2F3136
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)
        self.main = discord.Embed(
            color = self.color,
            title = f'__Geralt is Here to Help__',
            description =   f'Well hello there dear user <:AkkoHi:898611360580141097> ! My name is **[Geralt#9638](https://bsod2528.wixsite.com/geralt)** and I am a very simple **Discord Bot** alive just to induce fun into your server, and roast your members alive ! Use the dropdown for more information\n\n**CATEGORIES PRESENT -**\n\n'
                            f'>>> <:replygoin:897151741320122458> `BotUtils` - .ghelp BotUtils\n <:replygoin:897151741320122458> `Fun` - .ghelp Fun\n <:replygoin:897151741320122458> `Information` - .ghelp Information\n <:replygoin:897151741320122458> `Mod` - .ghelp Mod\n <:replygoin:897151741320122458> `Puns` - .ghelp Puns\n <:reply:897151692737486949> `Quotes` - .ghelp Quotes\n',
            timestamp = self.help.context.message.created_at)
        options = []
        for cog, commands in self.mapping.items():
            name = cog.qualified_name if cog else 'Essential'
            description = cog.description if cog else 'No Cog Present'
            if not name.startswith('On'):
                option = discord.SelectOption(
                    emoji = self.help.emojis.get(name) if self.help.emojis.get(name) else None, 
                    label = f'{name}', 
                    description = description, 
                    value = name)
                options.append(option)
        self.add_item(
            item = HelpMenuUI(
                placeholder = 'Choose your help category!', 
                options = options, 
                min_values = 1, 
                max_values = 1, 
                view = self))
    async def on_timeout(self):
        try:
            for item in self.children:
                if isinstance(item, discord.ui.Select):
                    item.placeholder = 'Dropdown disabled my friend ;('
                item.disabled = True
            await self.message.edit(view = self)
        except discord.NotFound:
            return

    async def interaction_check(self, interaction:discord.Interaction):
        if interaction.user.id == self.help.context.author.id:
            return True
        inter_check = discord.Embed(
            color = self.color,
            title = 'SIKE !!',
            description = f'<@{interaction.user.id}> ! <@{self.help.context.author.id}> INVOKED HELP, NOT YOU IDIOT !! ',
            timestamp = self.help.context.message.created_at
        )
        await interaction.response.send_message(embed = inter_check, ephemeral = True)
        return False
    
    @discord.ui.button(
        label = '\u2001\u2001\u2001\u2001Main Page\u2001\u2001\u2001\u2001',
        style = ButtonStyle.green)
    async def mainpage(self, button : discord.ui.button, interaction : discord.Interaction):
        await interaction.response.edit_message(embed = self.main)
    
    @discord.ui.button(
        label = '\u2001\u2001\u2001\u2001Delete\u2001\u2001\u2001\u2001',
        style = ButtonStyle.red)
    async def delete(self, button : discord.ui.button, interaction : discord.Interaction):
        await interaction.response.send_message('Alright, I will delete', ephemeral = True)
        await interaction.message.delete()
