import typing
import discord

from discord import Forbidden
from discord import app_commands
from discord.ext import commands

import Source.Kernel.Utilities.Crucial as Crucial
import Source.Kernel.Views.Interface as Interface
import Source.Kernel.Views.Paginator as Paginator

class Fun(commands.Cog):
    """Simple commands that induce Fun"""
    def __init__(self, bot):
        self.bot = bot
        self.delete = {} # -------
        self.pre_edit = {} #     |-- > Snipe command related dictionaries
        self.post_edit = {} # --=)

    # Listeners for "snipe" command
    @commands.Cog.listener()
    async def on_message_delete(self, message : discord.Message):
        self.delete[message.channel.id] = (message.content, message.author, message.channel.id, message.created_at)

    @commands.Cog.listener()
    async def on_message_edit(self, pre_edit : discord.Message, post_edit : discord.Message):
        self.pre_edit[pre_edit.channel.id] = (pre_edit.jump_url, pre_edit.content, pre_edit.author, pre_edit.channel.id, pre_edit.created_at)
        self.post_edit[post_edit.channel.id] = (post_edit.content, post_edit.author, post_edit.channel.id, post_edit.edited_at)

    # Mimics a user by sending a webhook as them.
    @commands.hybrid_command(
        name = "as", 
        brief = "Send a Webhook",
        with_app_command = True)
    @app_commands.guild_only()
    @app_commands.describe(user = "Select a user to mimic")    
    @app_commands.describe(message = "Type out the message you want to send.")
    @commands.guild_only()
    async def echo(self, ctx : commands.Context, user : discord.Member, *, message : str):
        """Send a webhook message as the user you mentioned"""
        if ctx.interaction:
            await ctx.interaction.response.defer(thinking = True, ephemeral = True)
            wbhk = await Crucial.fetch_webhook(ctx.channel)
            thread = discord.utils.MISSING
            if isinstance(ctx.channel, discord.Thread):
                thread = ctx.channel
            await wbhk.send(message, avatar_url = user.display_avatar.url, username = user.display_name, thread = thread)
            await ctx.send("Successfully sent <:NanoTick:925271358735257651>", ephemeral = True)
        else:
            wbhk = await Crucial.fetch_webhook(ctx.channel)
            thread = discord.utils.MISSING
            if isinstance(ctx.channel, discord.Thread):
                thread = ctx.channel
            await wbhk.send(message, avatar_url = user.display_avatar.url, username = user.display_name, thread = thread)
            await ctx.message.delete(delay = 0)
 
    # Snipe command as a group
    @commands.group(
        name = "snipe",
        aliases = ["s"])
    @commands.guild_only()
    async def snipe(self, ctx):
        """Get edited / deleted messages"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)
 
    # Snipes for deleted messages
    @snipe.command(
        name = "delete",
        brief = "Snipe Deleted Messages",
        aliases = ["del", "d"])
    async def snipe_delete(self, ctx : commands.Context):
        """Get the details of the recently deleted message"""
        try:    
            message, author, channel, time = self.delete[ctx.channel.id]    
            delete_emb = discord.Embed(
                title = "Sniped Deleted Message",
                description = f"**<:ReplyContinued:930634770004725821> - [Message Author :]({author.display_avatar.url})** {author.mention} (`{author.id}`)\n**<:ReplyContinued:930634770004725821> - In Channel :** <#{channel}> (`{channel}`)\n**<:Reply:930634822865547294> - Message Created At :** {self.bot.datetime(time)}",
                colour = self.bot.colour)
            delete_emb.add_field(
                name = "Message Content",
                value = f"```prolog\n{message}\n```")
            delete_emb.timestamp = discord.utils.utcnow()
            await ctx.reply(embed = delete_emb, allowed_mentions = self.bot.mentions)
        except:
            await ctx.reply("No one has deleted. any messages as of now <a:HumanBro:905748764432662549>", allowed_mentions = self.bot.mentions)
 
    # Snipes for edited messages
    @snipe.command(
        name = "edit",
        brief = "Snipe Edited Messages",
        aliases = ["ed", "e"])
    async def snipe_edit(self, ctx : commands.Context):
        """Get the details of the recently edited message"""
        try:    
            url, message, author, channel, pre_time = self.pre_edit[ctx.channel.id]    
            post_message, author, channel, post_time = self.post_edit[ctx.channel.id]    
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label = "Jump to Message", style = discord.ButtonStyle.link, url = url, emoji = "<a:ChainLink:936158619030941706>"))
            edit_emb = discord.Embed(
                title = "Sniped Edited Message",
                description = f"**<:ReplyContinued:930634770004725821> - [Message Author :]({author.display_avatar.url})** {author.mention} (`{author.id}`)\n**<:ReplyContinued:930634770004725821> - In Channel :** <#{channel}> (`{channel}`)\n**<:Reply:930634822865547294> - Message Sent At :** {self.bot.datetime(pre_time)}",
                colour = self.bot.colour)
            edit_emb.add_field(
                name = "Before Edit",
                value = f"```prolog\n{message}\n```")
            edit_emb.add_field(
                name = "After Edit",
                value = f"**<:Reply:930634822865547294> - Message Edited at :** {self.bot.datetime(post_time)}\n```prolog\n{post_message}\n```",
                inline = False)
            await ctx.reply(embed = edit_emb, allowed_mentions = self.bot.mentions, view = view)
        except:
            await ctx.reply("No one has edited any messages as of now <a:BotLurk:905749164355379241>", allowed_mentions = self.bot.mentions)
    
    @snipe.command(
        name = "list",
        brief = "Get a list of sniped messages",
        aliases = ["l"])
    async def snipe_list(self, ctx : commands.Context):
        """Get a list of all deleted and edited messages"""
        await ctx.send("hi", view = Interface.SnipeView(self.bot, ctx))

    @commands.command(
        name = "nitro",
        brief = "Gift Nitro")
    async def nitro(self, ctx : commands.Context, *, user : discord.Member = None):
        """Gift a user free nitro!"""
        try:
            if user is None:
                nitro_emb = discord.Embed(
                    title = "<a:Nitro:905661661191479326> Nitro Has Been Gifted!",
                    description = f">>> {ctx.author.mention} has been gifted nitro classic by {ctx.guild.me.mention} <a:WumpusHypesquad:905661121501990923>.\n<:Reply:930634822865547294> **-** **{ctx.author}** click on the button below to avail the nitro.",
                    colour = 0x2F3136)
                nitro_emb.set_thumbnail(url = "https://i.imgur.com/w9aiD6F.png")
                nitro_emb.timestamp = discord.utils.utcnow()    
                await ctx.send(embed = nitro_emb, view = Interface.Nitro(user))
            else:
                nitro_emb = discord.Embed(
                    title = "<a:Nitro:905661661191479326> Nitro Has Been Gifted!",
                    description = f">>> <@{user.id}> has been gifted nitro classic by {ctx.author.mention} <a:WumpusHypesquad:905661121501990923>.\n<:Reply:930634822865547294> **-** **{user}** click on the button below to avail the nitro.",
                    colour = 0x2F3136)
                nitro_emb.set_thumbnail(url = "https://i.imgur.com/w9aiD6F.png")
                nitro_emb.timestamp = discord.utils.utcnow()
                await ctx.send(embed = nitro_emb, view = Interface.Nitro(user))
        
        except Forbidden as F:
            raise commands.errors(F)

    @commands.command(
        name = "pop",
        brief = "Pop Buttons!")
    async def pop(self, ctx : commands.Context, *, size : str = None):
        """Fidget with the buttons by popping them!"""
        
        if size is None:
            pop_game = Interface.Pop(ctx)
            await pop_game.start()
        else:
            if size == "small":
                pop_game = Interface.Pop(ctx)
                await pop_game.start()
            elif size == "medium":
                pop_game = Interface.PopMedium(ctx)
                await pop_game.start()
            elif size == "large":
                pop_game = Interface.PopLarge(ctx)
                await pop_game.start()
            else:
                await ctx.reply(f"**{ctx.author}** - please mention a size. Your choices are :\n<:ReplyContinued:930634770004725821> - `small`\n<:ReplyContinued:930634770004725821> - `medium`\n<:Reply:930634822865547294> - `large`.")
    
    @commands.group(
        name = "click",
        brief = "Click and Win",
        aliases = ["cl"])
    @commands.guild_only()
    async def click(self, ctx : commands.Context):
        """Enjoy a nice satisfying game by clicking on the button!"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)
    
    @click.command(
        name = "start",
        brief = "Start a game of click")
    async def click_start(self, ctx : commands.Context, *, flag : typing.Optional[Interface.ClickSize]):
        if not flag:
            await Interface.ClickGame(self.bot, ctx, size = 1).send(ctx)
        if flag:
            await Interface.ClickGame(self.bot, ctx, size = flag.size).send(ctx)

    @click.command(
        name = "leaderboard",
        brief = "Check your rank",
        aliases = ["lb", "rank"])
    async def click_score(self, ctx : commands.Context):
        await Interface.ClickLeaderboard(self.bot, ctx).send()


async def setup(bot):
    await bot.add_cog(Fun(bot))