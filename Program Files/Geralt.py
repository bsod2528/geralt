import os
import webbrowser
import time
import random
from discord import activity, channel, mentions, user
from discord.embeds import EmptyEmbed
from discord.flags import Intents
from discord.types.embed import EmbedField
import requests
import discord
import random
import sys
import asyncio
import datetime
import logging
import pathlib
import json
from discord import DMChannel
from discord import message
from discord.enums import ContentFilter, T
from discord.errors import Forbidden
from discord.ext import commands
from discord.ext import tasks
from discord.utils import find
from itertools import cycle
from discord.ext.commands.core import command, has_guild_permissions, has_permissions
from jishaku.cog import Jishaku
from jishaku.cog import STANDARD_FEATURES, OPTIONAL_FEATURES
from jishaku.features.python import PythonFeature
from jishaku.features.root_command import RootCommand
from jishaku.features.baseclass import Feature
from googleapiclient.discovery import build
from typing import Coroutine, Optional, Union

from discord import ui, Interaction, SelectOption, ButtonStyle, Embed
from discord.ext.commands import Cog, Command, Group, DefaultHelpCommand
	
class Bot(commands.Bot):
	def __init__(self, **kwargs):
		super().__init__(command_prefix = ['.g'], status = discord.Status.do_not_disturb, intents = discord.Intents.all(),activity = discord.Game(name = f'.ghelp ; i hate myself'))
		
	async def on_ready(self):
		print(f'\n\nCame into life as {self.user} (ID: {self.user.id})')
		total_members = list(bot.get_all_members())
		total_channels = sum(1 for x in bot.get_all_channels())
		print(f'Number of Guilds : {len(bot.guilds)}')
		print(f'Number of Large Guilds : {sum(g.large for g in bot.guilds)}')
		print(f'Number of Chunked Guilds : {sum(g.chunked for g in bot.guilds)}')
		print(f'Count of Total Members : {len(total_members)}')
		print(f'Channels Im In : {total_channels}')
		print(f'Message Cache Size : {len(bot.cached_messages)}\n')
		print(f'Geralt is ready for action !')
		
bot = Bot()

rootdir = pathlib.Path(__file__).parent.resolve()

logger = logging.getLogger('Geralt')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='Geralt.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
def av(ctx):
	return ctx.author.id == 750979369001811982 , 760823877034573864

Entity = Optional[Union[Cog, Command]]
class EmbedHelp(commands.HelpCommand):
	def get_command_signature(self, command, ctx):
		return '{0.qualified_name} {0.signature}'.format(command)

	async def send_view(self, embed: Embed, entity: Entity):
		mapping = await self.get_filtered_mapping()
		view = HelpView(self, mapping, entity)
		await view.update_commands()  # must be async to filter subcommands
		view.message = await self.get_destination().send(
			embed=embed,
			view=view)

	async def send_bot_help(self, mapping):
		emb = discord.Embed(
			title = '__***Geralt is Here to Help***__', 
			color = discord.Color.from_rgb(117, 128, 219))
		description = self.context.bot.description
		if description:
			emb.description = description

		for cog, commands in mapping.items():
			name = 'Essential' if cog is None else cog.qualified_name
			filtered = await self.filter_commands(commands, sort = True)
			if filtered:
				value = '\u2002'.join(c.name for c in commands)
				if cog and cog.description:
					value = '{0}\n{1}'.format(cog.description, value)

				emb.add_field(
					name = f'*{name}*', 
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
				value=command.short_doc or 'Short Documentation yet to be provided', 
				inline=False)
			embed.set_footer(text=self.get_ending_note())
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
		await self.get_destination().send(embed=embed)
	send_command_help = send_group_help
	
	async def on_help_command_error(self, ctx, error):
		if isinstance(error, commands.BadArgument):
			embed = discord.Embed(title="Error", description=str(error))
			await ctx.send(embed=embed)


from typing import Coroutine, Optional, Union

from discord import ui, Interaction, SelectOption, ButtonStyle, Embed
from discord.ext.commands import Cog, Command, Group, DefaultHelpCommand


BotMapping = dict[Optional[Cog], list[Command]]
Entity = Optional[Union[Cog, Command]]


class ComponentHelp(DefaultHelpCommand):
	_mapping = None

	async def get_filtered_mapping(self) -> BotMapping:
		if self._mapping is None:
			mapping = {cog: await self.filter_commands(cmds)
				   for cog, cmds in self.get_bot_mapping().items()}
			# filter out cogs with no commands post-filter
			self._mapping = {cog: cmds for cog, cmds in mapping.items() if cmds}
		return self._mapping

	async def send_view(self, embed: Embed, entity: Entity):
		mapping = await self.get_filtered_mapping()
		view = HelpView(self, mapping, entity)
		await view.update_commands()  # must be async to filter subcommands
		view.message = await self.get_destination().send(
			embed=embed,
			view=view)
		Embedcolor = discord.Color.from_rgb(117, 128, 219),

	async def send_bot_help(self, mapping: BotMapping):
		mapping = await self.get_filtered_mapping()
		embed = await self.get_bot_help(mapping)
		await self.send_view(embed, None)
	async def send_cog_help(self, cog: Cog):
		mapping = await self.get_filtered_mapping()
		if cog not in mapping:
			return

		embed = await self.get_cog_help(cog)
		await self.send_view(embed, cog)

	async def send_group_help(self, group: Group):
		embed = await self.get_group_help(group)
		await self.send_view(embed, group)

	async def send_command_help(self, command: Command):
		embed = await self.get_command_help(command)
		await self.send_view(embed, command)

	# These are just simple bare-minimum implementationss,
	# you probably want to rewrite all of these.

	async def get_bot_help(self, mapping: BotMapping) -> Embed:
		cogs = sorted(cog.qualified_name for cog in mapping if cog)
		commands = [f'`{cmd}`' for cmd in mapping[None]]

		description = '\n'.join(['Categories:',
								 '\n'.join(cogs),
								 f'\n{self.no_category}:',
								 '\n'.join(commands)])

		return Embed(title='Categories', description=description)

	async def get_cog_help(self, cog: Cog) -> Embed:
		mapping = await self.get_filtered_mapping()
		commands = mapping[cog]
		return Embed(title=f'{cog.qualified_name} Commands',
					 description='\n'.join(f'`{cmd}`' for cmd in commands))

	async def get_group_help(self, group: Group) -> Embed:
		commands = await self.filter_commands(group.commands)

		description =  self.get__signature(command), 

		return Embed(
			title = f'__Command :*{group}*__', 
			description = description,
			color =  discord.Color.from_rgb(117, 128, 219))

	async def get_command_help(self, command: Command) -> Embed:
		description = command.help
		return Embed(
			title = f'__Command: *{command}*__', 
			description = description,
			color =  discord.Color.from_rgb(117, 128, 219))
		

class HelpView(ui.View):
	def __init__(self, help: EmbedHelp,
				 mapping: BotMapping,
				 entity: Entity = None,
				 *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.help = help
		self.bot = help.context.bot

		self.mapping = mapping
		self.entity = entity

		self.update_cogs()

	async def on_timeout(self):
		await self.message.delete()

	def update_cogs(self):
		# to use emojis, you can build a list of `SelectOptions` then sort by label
		names = sorted(cog.qualified_name for cog in self.mapping if cog)
		# always add "No Category" at the end
		names.append(self.help.no_category)
		options = [SelectOption(label=name) for name in names]
		self.children[0].options = options

	async def update_commands(self):
		entity = self.entity

		# list the parent command/cog/bot's commands instead of nothing
		if isinstance(entity, Command) and not isinstance(entity, Group):
			entity = entity.parent or entity.cog or None

		if isinstance(entity, Group):
			cmds = await self.help.filter_commands(entity.commands)
		else:
			cmds = self.mapping[entity]

		options = [SelectOption(label=f'{cmd}') for cmd in cmds]
		self.children[1].options = options

	def get_embed(self) -> Coroutine[None, None, Embed]:
		entity = self.entity
		if isinstance(entity, Cog):
			return self.help.get_cog_help(entity)
		elif isinstance(entity, Group):
			return self.help.get_group_help(entity)
		elif isinstance(entity, Command):
			return self.help.get_command_help(entity)
		else:
			return self.help.get_bot_help(self.mapping)

	async def respond_with_edit(self, interaction: Interaction):
		embed = await self.get_embed()
		await interaction.response.edit_message(embed=embed, view=self)

	@ui.select(placeholder='Help Command Menu')
	async def cog_select(self, select: ui.Select, interaction: Interaction):
		name = select.values[0]
		entity = self.bot.get_cog(name)
		if entity == self.entity:
			return
		self.entity = entity

		await self.update_commands()
		await self.respond_with_edit(interaction)

	@ui.button(label='Up', style=ButtonStyle.blurple)
	async def up_level(self, button: ui.Button, interaction: Interaction):
		if isinstance(self.entity, Command):
			self.entity = self.entity.parent or self.entity.cog or None
		elif isinstance(self.entity, Cog):
			self.entity = None
		else:
			return
		await self.update_commands()
		await self.respond_with_edit(interaction)

	@ui.button(label='Close', style=ButtonStyle.danger)
	async def close(self, button: ui.Button, interaction: Interaction):
		self.stop()
		await interaction.message.delete()

for filename in os.listdir(f'{rootdir}/cogs'):
	if filename.endswith('.py'):    
			bot.load_extension(f'cogs.{filename[:-3]}')

bot.help_command = EmbedHelp()


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

token = json.load(open(r'Program Files\config.json'))
bot.run(f'{token["TOKEN"]}')