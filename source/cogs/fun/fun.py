import discord

from discord import app_commands
from discord.ext import commands
from typing import Dict, List, Optional
from discord import Forbidden, NotFound

from ...kernel.subclasses.bot import Geralt
from ...kernel.subclasses.embed import BaseEmbed
from ...kernel.subclasses.context import GeraltContext
from ...kernel.views.fun import Pop, Nitro, ClickGame, PopSize, ClickSize, ClickLeaderboard, MemoryGame, MemoryDifficulty


class Fun(commands.Cog):
    """Simple commands that induce Fun"""

    def __init__(self, bot: Geralt):
        self.bot: Geralt = bot
        self.delete: Dict = {}  # -------
        self.pre_edit: Dict = {}  # |-- > Snipe command related dictionaries
        self.post_edit: Dict = {}  # --=)

    @property
    def emote(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(
            name="Fun", id=905754435379163176, animated=True)

    # Listeners for "snipe" command
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        self.delete[message.channel.id] = (
            message.content, message.author, message.channel.id, message.created_at)

    @commands.Cog.listener()
    async def on_message_edit(self, pre_edit: discord.Message, post_edit: discord.Message):
        self.pre_edit[pre_edit.channel.id] = (
            pre_edit.jump_url, pre_edit.content, pre_edit.author, pre_edit.channel.id, pre_edit.created_at)
        self.post_edit[post_edit.channel.id] = (
            post_edit.content, post_edit.author, post_edit.channel.id, post_edit.edited_at)

    # Mimics a user by sending a webhook as them.
    @commands.hybrid_command(
        name="as",
        brief="Send a Webhook",
        with_app_command=True)
    @commands.guild_only()
    @app_commands.guild_only()
    @commands.cooldown(3, 5, commands.BucketType.user)
    @app_commands.describe(user="Select a user to mimic")
    @app_commands.describe(message="Type out the message you want to send.")
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    async def echo(self, ctx: GeraltContext, user: discord.Member, *, message: str) -> Optional[discord.Message]:
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
                thread=thread)
            if ctx.interaction:
                await ctx.send("Successfully sent <:NanoTick:925271358735257651>")
            await ctx.message.delete(delay=0)
        except NotFound:
            return await ctx.send(f"{ctx.author.mention} ─ please try again later. Either your internet is slow or mine is \U0001f91d")

    # Snipe command as a group
    @commands.group(
        name="snipe",
        aliases=["s"])
    @commands.cooldown(3, 5, commands.BucketType.user)
    @commands.guild_only()
    async def snipe(self, ctx: GeraltContext) -> Optional[discord.Message]:
        """Get edited / deleted messages"""
        if ctx.invoked_subcommand is None:
            await ctx.command_help()

    # Snipes for deleted messages
    @snipe.command(
        name="delete",
        brief="Snipe Deleted Messages",
        aliases=["del", "d"])
    @commands.cooldown(3, 5, commands.BucketType.user)
    async def snipe_delete(self, ctx: GeraltContext) -> Optional[discord.Message]:
        """Get the details of the recently deleted message"""
        try:
            message, author, channel, time = self.delete[ctx.channel.id]
            delete_emb = BaseEmbed(
                title="Sniped Deleted Message",
                description=f"**<:ReplyContinued:930634770004725821> - [Message Author :]({author.display_avatar.url})** {author.mention} (`{author.id}`)\n**<:ReplyContinued:930634770004725821> - In Channel :** <#{channel}> (`{channel}`)\n**<:Reply:930634822865547294> - Message Created At :** {self.bot.timestamp(time, style='R')}",
                colour=0x2F3136)
            delete_emb.add_field(
                name="Message Content",
                value=f">>> {message}")
            await ctx.reply(embed=delete_emb, allowed_mentions=self.bot.mentions)
        except BaseException:
            await ctx.reply("No one has deleted. any messages as of now <a:HumanBro:905748764432662549>", allowed_mentions=self.bot.mentions)

    # Snipes for edited messages
    @snipe.command(
        name="edit",
        brief="Snipe Edited Messages",
        aliases=["ed", "e"])
    @commands.cooldown(3, 5, commands.BucketType.user)
    async def snipe_edit(self, ctx: GeraltContext) -> Optional[discord.Message]:
        """Get the details of the recently edited message"""
        try:
            url, message, author, channel, pre_time = self.pre_edit[ctx.channel.id]
            post_message, author, channel, post_time = self.post_edit[ctx.channel.id]
            view = discord.ui.View()
            view.add_item(
                discord.ui.Button(
                    label="Jump to Message",
                    style=discord.ButtonStyle.link,
                    url=url,
                    emoji="<a:ChainLink:936158619030941706>"))
            edit_emb = BaseEmbed(
                title="Sniped Edited Message",
                description=f"**<:ReplyContinued:930634770004725821> - [Message Author :]({author.display_avatar.url})** {author.mention} (`{author.id}`)\n**<:ReplyContinued:930634770004725821> - In Channel :** <#{channel}> (`{channel}`)\n**<:Reply:930634822865547294> - Message Sent At :** {self.bot.timestamp(pre_time, style='R')}",
                colour=0x2F3136)
            edit_emb.add_field(
                name="Before Edit",
                value=f">>> {message}")
            edit_emb.add_field(
                name="After Edit",
                value=f"**<:Reply:930634822865547294> - Message Edited at :** {self.bot.timestamp(post_time, style='R')}\n>>> {post_message}",
                inline=False)
            await ctx.reply(embed=edit_emb, allowed_mentions=self.bot.mentions, view=view)
        except BaseException:
            await ctx.reply("No one has edited any messages as of now <a:BotLurk:905749164355379241>", allowed_mentions=self.bot.mentions)

    @commands.command(
        name="nitro",
        brief="Gift Nitro")
    @commands.cooldown(3, 3, commands.BucketType.user)
    async def nitro(self, ctx: GeraltContext, *, user: discord.Member = None) -> Optional[discord.Message]:
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

    @commands.command(
        name="pop",
        brief="Pop Buttons!")
    @commands.cooldown(3, 5, commands.BucketType.user)
    async def pop(self, ctx: GeraltContext, *, flag: Optional[PopSize]) -> Optional[discord.Message]:
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
        aliases=["cl", "clock"])
    @commands.guild_only()
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def click(self, ctx: GeraltContext) -> Optional[discord.Message]:
        """Just click the button!"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @click.command(
        name="start",
        brief="Start a game of click")
    @commands.cooldown(2, 10, commands.BucketType.user)
    async def click_start(self, ctx: GeraltContext, *, flag: Optional[ClickSize]) -> Optional[discord.Message]:
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
        aliases=["lb", "rank"])
    @commands.cooldown(3, 5, commands.BucketType.user)
    async def click_score(self, ctx: GeraltContext) -> Optional[discord.Message]:
        await ClickLeaderboard(self.bot, ctx).send()

    @commands.hybrid_command(
        name="memory-game",
        brief="Simple Memory Game",
        aliases=["monkey-game", "mem", "monke"])
    @app_commands.rename(flag="difficulty-level")
    @app_commands.describe(flag="Start with `--difficulty`")
    @commands.cooldown(3, 10, commands.BucketType.user)
    async def monkey_memory(self, ctx: GeraltContext, *, flag: Optional[MemoryDifficulty]) -> Optional[discord.Message]:
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