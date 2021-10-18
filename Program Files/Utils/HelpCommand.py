import datetime
import discord
from discord.ext import commands

class HelpViewUI(discord.ui.Select):
    def __init__(self, view, **kwargs):
        super().__init__(**kwargs)
        self.help = view.help
        self.mapping = view.mapping
        self.mainhelp = view.mainhelp
        def get_command_signature(self, command, ctx):

            async def callback(self, interaction : discord.Interaction):
                for cog, commands in self.mapping.items():
                    name = 'Essential' if cog is None else cog.qualified_name
                    description = 'Command does not have a Category' if cog.description is None else cog.description 
                    cmd = cog.walk_commands() if cog else command
                    if self.values[0] == name:
                        emb = discord.Embed(
                            title = F'Help',
                            color = discord.Color.from_rgb(117, 128, 219),
                            description=F"{description}\n\n{''.join(self.gts(command) for command in cmd)}",
                            timestamp=self.help.context.message.created_at)
                        await interaction.response.edit_message(embed = emb)

                    options = []
                    for cog, commands in self.mapping.items():
                        name = 'Essential' if cog is None else cog.qualified_name
                        description = 'Command does not have a Category' if cog.description is None else cog.description 
                        if not name.startswith('ON'):
                            option = discord.SelectOption(
                                label = F'{name} Category',     
                                description = description, 
                                value = name)
                        self.add_item(
                            item = HelpViewUI(
                                placeholder ='Choose your category', 
                                options = options, 
                                min_values = 1, 
                                max_values = 1, 
                                view = self))

class HelpView(discord.ui.View):
    def __init__(self, mapping, help):
        super().__init__(placeholder ='Choose your category')
        self.help = help
        self.mapping = mapping
        self.main = discord.Embed(
            title = '__***Geralt is Here to Help***__',
            color = discord.Color.from_rgb(117, 128, 219),
            description = 'Use the Select Menu for a list of commands present!')

        
class SelectMenuHelp(commands.HelpCommand):
    def __init__(self):
        self.color = discord.Color.from_rgb(117, 128, 219)
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)
        super().__init__()
        def get_command_signature(self, command, ctx):
        
            async def send_bot_help(self, mapping):
                view = HelpView.SelectView(self, mapping)
                view.mainhelp.add_field(
                    name = 'Small Sescription',
                    value = 'What am I?\n I am DA BOT!')
                view.message = await self.context.send(content='Hello', embed=view.mainhelp, view=view)
                return

            async def send_cog_help(self, cog):
                cogemb = discord.Embed(
                    title = f'{cog.qualified_name}',
                    description = f'{cog.description}\n',
                    color = self.color)
                cogemb.timestamp = self.timestamp

                for cog in cog.walk_commands():
                    cogemb.description += f'{self.get_command_signature(command)}'
                await self.context.send(embed = cogemb)

            async def send_command_help(self, command):
                cmdemb = discord.Embed(
                    title = self.get_command_signature(command),
                    description = command.help or 'Description yet to be provided',
                    color = self.color)
                if cog := command.cog:
                    cmdemb.add_field(
                        name = 'Category',
                        value = f'{cog.qualified_name}')
                await self.context.send(embed = cmdemb) 