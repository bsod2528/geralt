import discord, requests, random, sys, asyncio, datetime, logging, json, pathlib, asyncpg, webbrowser, os, time
import Kernel.HelpCommand.Help as help
from discord.components import Button
from discord import activity, channel, mentions, user
from discord.embeds import EmptyEmbed
from discord.flags import Intents
from discord.types.embed import EmbedField
from discord.ui import view
from google.auth import credentials
from discord import DMChannel, message
from discord.enums import ContentFilter
from discord.ext import commands
from discord.ext import tasks
from discord.utils import find
from discord.ext.commands.core import command, has_guild_permissions, has_permissions
from typing import Coroutine, Optional, Union
import Kernel.Utils.Buttons as Buttons
from discord import ui, Interaction, SelectOption, ButtonStyle, Embed
from discord.ext.commands import Cog, Command, Group, DefaultHelpCommand
	
class Geralt(commands.Bot):
	def __init__(self, **kwargs):
		super().__init__(
			command_prefix = ['.g'], 
			status = discord.Status.idle, 
			intents = discord.Intents.all(),
			activity = discord.Game(name = 'jls'))

	async def on_ready(self):
		print(f'\n\nCame into life as {self.user} (ID: {self.user.id})')
		total_members = list(bot.get_all_members())
		total_channels = sum(1 for x in bot.get_all_channels())
		chunk_guilds_on_startup = True,
		case_insensitive = True,
		print(f'Number of Guilds : {len(bot.guilds)}')
		print(f'Number of Large Guilds : {sum(g.large for g in bot.guilds)}')
		print(f'Number of Chunked Guilds : {sum(g.chunked for g in bot.guilds)}')
		print(f'Count of Total Members : {len(total_members)}')
		print(f'Channels Im In : {total_channels}')
		print(f'Message Cache Size : {len(bot.cached_messages)}\n')
		print(f'Geralt is ready for action !')
		await self.change_presence(status = discord.Status.idle, activity = discord.Game(name = '.ghelp ; i hate my self'))

bot = Geralt()

rootdir = pathlib.Path(__file__).parent.resolve()

logger = logging.getLogger('Geralt')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='Geralt.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

def av(ctx):
	return ctx.author.id == 750979369001811982 , 760823877034573864

async def on_run():
	dbkey = {
		"user"	:	"bsod",
		"password"	:	"VPVS",
		"database"	:	"geralt",
		"host"	:	"127.0.0.1"
		}
	db = await asyncpg.create_pool(**dbkey)
	await db.execute("CREATE TABLE IF NOT EXISTS users(id bigint PRIMARY KEY, data text);")
	
class Help(commands.HelpCommand):
	def get_command_signature(self, command, ctx):
    		return '{0.qualified_name} {0.signature}'.format(command)

	async def send_bot_help(self, mapping):
		emb = discord.Embed(
			title = '__***Geralt is Here to Help***__', 
			color = discord.Color.from_rgb(117, 128, 219))
		description = self.context.bot.description
		if description:
			emb.description = description

		for cog, commands in mapping.items():
			name = '<:reply:897151692737486949>Essential' if cog is None else f'<:reply:897151692737486949>{cog.qualified_name}'
			filtered = await self.filter_commands(commands, sort = True)
			if filtered:
				value = '\u2002'.join(c.name for c in commands)
				if cog and cog.description:
					value = '{0}\n{1}'.format(cog.description, value)
				emb.add_field(
					name = f'{name}', 
					value = f'{value}',
					inline = False)
				emb.set_footer(
					text = 'Run .ginfo for dashboard')
				emb.timestamp = datetime.datetime.now(datetime.timezone.utc)
		await self.get_destination().send(embed = emb)
	
	async def send_cog_help(self, cog):
		embed = discord.Embed(title='{0.qualified_name} Commands'.format(cog), colour=discord.Color.from_rgb(117, 128, 219))
		if cog.description:
			embed.description = cog.description

		filtered = await self.filter_commands(cog.get_commands(), sort=True)
		for command in filtered:
			embed.add_field(
				name = self.get_command_signature(command), 
				value = command.short_doc or 'Short Documentation yet to be provided', 
				inline = False)
			embed.set_footer(text = self.get_ending_note())
		await self.get_destination().send(embed=embed)

	async def send_group_help(self, group):
		embed = discord.Embed(
			title = f'__Command : *{group.qualified_name}*__',
			color = discord.Color.from_rgb(117, 128, 219))
		embed.set_footer(
			text = '.ghelp [command] for more info on each command')
		if group.help:
			embed.description = group.help

		if isinstance(group, commands.Group):
			filtered = await self.filter_commands(group.commands, sort = True)
			for command in filtered:
				embed.add_field(
					name = self.get_command_signature(command), 
					value = command.short_doc or 'Short Documentation yet to be provided', 
					inline = False)
		await self.get_destination().send(embed = embed)
	send_command_help = send_group_help
	
	async def on_help_command_error(self, ctx, error):
		if isinstance(error, commands.BadArgument):
			embed = discord.Embed(title="Error", description=str(error))
			await ctx.send(embed=embed)
bot.help_command = help.CustomHelp()

for filename in os.listdir(f'{rootdir}/Cogs'):
	if filename.endswith('.py'):    
			bot.load_extension(f'Cogs.{filename[:-3]}')

received = 880128519110262794
@bot.event
async def on_message(message: discord.Message):
	channel = bot.get_channel(received)
	if message.guild is None and not message.author.bot:
		emb = discord.Embed(
			title = 'My DMs',
			description = f'{message.author.mention} sent ➜ \n " *{message.content}* "' ,
			color = discord.Color.from_rgb(117, 128, 219))
		emb.timestamp = datetime.datetime.now(datetime.timezone.utc)
		await channel.send(embed = emb)
	await bot.process_commands(message)

@bot.event
async def on_message(message):
	if message.content == '<@!873204919593730119>':
    		await message.channel.send(f'{bot.help_command}')
	await bot.process_commands(message)


token = json.load(open(r'Program Files\Key.json'))
bot.run(f'{token["TOKEN"]}')