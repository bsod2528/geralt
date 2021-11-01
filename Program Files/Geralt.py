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