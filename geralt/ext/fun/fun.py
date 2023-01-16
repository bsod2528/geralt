from typing import List, Optional

import aiohttp
import discord
from discord import Forbidden, NotFound, app_commands
from discord.ext import commands

from ...bot import BaseBot
from ...context import BaseContext
from ...embed import BaseEmbed
from ...kernel.views.fun import (ClickGame, ClickLeaderboard, ClickSize,
                                 MemoryDifficulty, MemoryGame, Nitro, Pop,
                                 PopSize)
from ...kernel.views.paginator import Paginator


class Fun(commands.Cog):
    """Simple commands that induce Fun"""

    def __init__(self, bot: BaseBot):
        self.bot: BaseBot = bot

    @property
    def emote(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(
            name="Fun",
            id=905754435379163176,
            animated=True)

    # Mimics a user by sending a webhook as them.
    @commands.hybrid_command(
        name="as",
        brief="Send a Webhook",
        with_app_command=True)
    @commands.guild_only()
    @app_commands.guild_only()
    @commands.cooldown(3, 5, commands.BucketType.user)
    @app_commands.describe(user="Select a user to mimic")
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    @app_commands.describe(attachment="Upload a file to send.")
    @app_commands.describe(message="Type out the message you want to send.")
    async def echo(self, ctx: BaseContext, user: discord.Member, attachment: Optional[discord.Attachment], *, message: str) -> Optional[discord.Message]:
        """Send a webhook message as the user you mentioned"""
        try:
            if ctx.interaction:
                await ctx.interaction.response.defer(thinking=True, ephemeral=True)
            wbhk = await self.bot.webhook_manager.create_webhook(ctx.channel)
            thread = discord.utils.MISSING
            if isinstance(ctx.channel, discord.Thread):
                thread = ctx.channel
            await wbhk.send(
                message,
                avatar_url=user.display_avatar.url,
                username=user.display_name,
                file=await attachment.to_file() if attachment else discord.utils.MISSING,
                thread=thread)
            if ctx.interaction:
                await ctx.send("Successfully sent <:NanoTick:925271358735257651>")
            await ctx.message.delete(delay=0)
        except NotFound:
            return await ctx.send(f"{ctx.author.mention} ─ please try again later. Either your internet is slow or mine is \U0001f91d")

    @commands.command(
        name="nitro",
        brief="Gift Nitro")
    @commands.cooldown(3, 3, commands.BucketType.user)
    async def nitro(self, ctx: BaseContext, *, user: discord.Member = None) -> Optional[discord.Message]:
        """Gift a user free nitro!"""
        try:
            nitro_emb = BaseEmbed(
                title="<a:Nitro:905661661191479326> Nitro Has Been Gifted!",
                colour=0x2F3136)
            nitro_emb.set_thumbnail(url="https://i.imgur.com/w9aiD6F.png")

            if user is None:
                nitro_emb.description = f">>> {ctx.author.mention} has been gifted nitro classic by {ctx.guild.me.mention} <a:WumpusHypesquad:905661121501990923>.\n**{ctx.author}** click on the button below to avail the nitro."
                await ctx.send(embed=nitro_emb, view=Nitro(ctx))
            else:
                nitro_emb.description = f">>> <@{user.id}> has been gifted nitro classic by {ctx.author.mention} <a:WumpusHypesquad:905661121501990923>.\n**{user}** click on the button below to avail the nitro."
                await ctx.send(embed=nitro_emb, view=Nitro(ctx))

        except Forbidden as F:
            raise commands.errors(F)

    @commands.hybrid_command(
        name="pop",
        brief="Pop Buttons!",
        with_app_command=True)
    @app_commands.describe(
        flag="Add more buttons: --size <int> | Maximum buttons allowed is 25.")
    @commands.cooldown(3, 5, commands.BucketType.user)
    async def pop(self, ctx: BaseContext, *, flag: Optional[PopSize]) -> Optional[discord.Message]:
        """Fidget with the buttons by popping them!
        ────
        **Flags Present :**
        `--size` : Sends that many number of buttons to pop.
        **Example :**
        `.gpop [--size 10]` Max size is `25` \U0001f44d
        ────"""
        if not flag:
            await Pop(ctx, size=1).send()
        if flag:
            await Pop(ctx, size=flag.size).send()

    @commands.hybrid_group(
        name="click",
        brief="Click and Win",
        aliases=["cl", "clock"],
        with_app_command=True)
    @commands.guild_only()
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def click(self, ctx: BaseContext) -> Optional[discord.Message]:
        """Just click the button!"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @click.command(
        name="start",
        brief="Start a game of click",
        with_app_command=True)
    @commands.cooldown(2, 10, commands.BucketType.user)
    @app_commands.describe(
        flag="Add more buttons: --size <int> | Maximum buttons allowed is 10.")
    async def click_start(self, ctx: BaseContext, *, flag: Optional[ClickSize]) -> Optional[discord.Message]:
        """Start a game of click.
        ────
        **Flags Present :**
        `--size` : Sends that many number of buttons to click.
        <:Join:932976724235395072> **Size Limit :** `10` \U0001f44d
        **Example :**
        `.gclick start [--size 10]`
        ────"""
        if not flag:
            await ClickGame(self.bot, ctx, size=1).send(ctx)
        if flag:
            if not flag.size:
                return await ctx.reply(f"Please pass in a number for the number of buttons you want : `{ctx.clean_prefix}click start --size [int]`. Maximum buttons is 10.")
            await ClickGame(self.bot, ctx, size=flag.size).send(ctx)

    @click.command(
        name="leaderboard",
        brief="Check your rank",
        aliases=["lb", "rank"],
        with_app_command=True)
    @commands.cooldown(3, 5, commands.BucketType.user)
    async def click_score(self, ctx: BaseContext) -> Optional[discord.Message]:
        await ClickLeaderboard(self.bot, ctx).send()

    @commands.hybrid_command(
        name="memory-game",
        brief="Simple Memory Game",
        aliases=["monkey-game", "mem", "monke"],
        with_app_command=True)
    @app_commands.rename(flag="difficulty-level")
    @app_commands.describe(flag="Start with `--difficulty`")
    @commands.cooldown(3, 10, commands.BucketType.user)
    async def monkey_memory(self, ctx: BaseContext, *, flag: Optional[MemoryDifficulty]) -> Optional[discord.Message]:
        """Play the Monkey Memory Game!
        ────
        **Flags Present :**
        `--difficulty` : Sets the difficulty level.
        <:Join:932976724235395072> **Aliases :** `--diff`
        <:Join:932976724235395072> **Levels :** [`easy`, `medium`, `hard`]
        **Example :**
        `.gmemory-game [--difficulty easy]`
        ────"""
        if not flag:
            view = MemoryGame("easy", ctx, 10)
            view.message = await ctx.reply(f"You have **{30 + (10* 5)}** seconds to finish it!", view=view, allowed_mentions=self.bot.mentions)
            await view.start()
        if flag:
            difficulty: List = ["easy", "medium", "hard"]
            if flag.difficulty not in difficulty:
                return await ctx.reply(f"**{ctx.author}** - These are your difficulty options:\n>>> ` - ` `easy`\n` - ` `medium`\n` - ` `hard`\n\n`{ctx.clean_prefix}{ctx.command.name} --difficulty [easy|medium|hard]`")
            if flag.difficulty in difficulty:
                if flag.difficulty == difficulty[0]:
                    easy_view = MemoryGame("easy", ctx, 10)
                    easy_view.message = await ctx.reply(f"You have **{30 + (10* 5)}** seconds to finish it!", view=easy_view, allowed_mentions=self.bot.mentions)
                    await easy_view.start()
                if flag.difficulty == difficulty[1]:
                    medium_view = MemoryGame("medium", ctx, 16)
                    medium_view.message = await ctx.reply(f"You have **{30 + (15* 5)}** seconds to finish it!", view=medium_view, allowed_mentions=self.bot.mentions)
                    await medium_view.start()
                if flag.difficulty == difficulty[2]:
                    hard_view = MemoryGame("hard", ctx, 20)
                    hard_view.message = await ctx.reply(f"You have **{30 + (20* 5)}** seconds to finish it!", view=hard_view, allowed_mentions=self.bot.mentions)
                    await hard_view.start()

    @commands.hybrid_command(
        name="urban",
        brief="Learn Gen-Z Language.",
        aliases=["ud"],
        with_app_command=True)
    @app_commands.describe(term="The Term which you want the urban meaning of.")
    async def urban(self, ctx: BaseContext, *, term: str) -> Optional[discord.Message]:
        """Search the `Urban Dictionary`."""
        try:
            async with self.bot.session.get(
                    url="http://api.urbandictionary.com/v0/define",
                    params={"term": term}) as response:

                if response.status != 200:
                    return await ctx.reply(f"**{ctx.author}** - An error occurred while connecting to Urban Dictionary:\n> **Status**: {response.status}\n? **Reason**: {response.reason}")

                json_data = await response.json()
                data = json_data.get("list", [])
                if not data:
                    return await ctx.reply(f"**{ctx.author}** - I was unable to find the definition for the term: `{term.strip()}`")

                embed_list: List[BaseEmbed] = []
                for results in data:
                    definition = results["definition"].replace(
                        "[", "").replace("]", "")
                    definition = definition if len(
                        definition) < 1024 else f"{definition[:1000]} . . ."

                    urban_definition_embs = BaseEmbed(
                        title=f"Meaning for `{results['word']}`",
                        url=results["permalink"],
                        colour=self.bot.colour)
                    urban_definition_embs.add_field(
                        name="<:GeraltRightArrow:904740634982760459> Description:",
                        value=f">>> {definition}")
                    urban_definition_embs.add_field(
                        name="<:Join:932976724235395072> Votes:",
                        value=f"> <:Reply:930634822865547294> <:Upvote:1037358225458212914> `{results['thumbs_up']}` | <:Downvote:1037358281288597594> `{results['thumbs_down']}`",
                        inline=False)
                    urban_definition_embs.add_field(
                        name="<:Join:932976724235395072> Extra Info.:",
                        value=f"> <:ReplyContinued:930634770004725821> Written By: `{results['author']}`\n> <:Reply:930634822865547294> Written On: {self.bot.timestamp(discord.utils.parse_time(results['written_on'][:-1]), style='D')}",
                        inline=False)
                    urban_definition_embs.set_footer(
                        text=f"Invoked By: {ctx.author}",
                        icon_url=ctx.author.display_avatar.url)
                    embed_list.append(urban_definition_embs)
                await Paginator(self.bot, ctx, embeds=embed_list).send(ctx)
        except aiohttp.client_exceptions.ClientConnectionError:
            return await ctx.reply(f"I wasn't able to connect to **Urban Dictionary** due to poor network. Please try again later <:YunoPensive:975215987542593556>")
