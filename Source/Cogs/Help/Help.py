import discord

from discord.ext import commands

class MyNewHelp(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        for page in self.paginator.pages:
            emby = discord.Embed(description=page, colour = 0x2F3136)
            await destination.send(embed=emby)

class CustomHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        help_command = MyNewHelp()
        help_command.cog = self
        bot.help_command = help_command
        
    async def cog_unload(self):
        self.bot.help_command = self._original_help_command
        
async def setup(bot):
    await bot.add_cog(CustomHelp(bot))