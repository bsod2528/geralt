import discord

from discord import Forbidden
from discord.ext import commands

import Source.Kernel.Utilities.Crucial as crucial
import Source.Kernel.Views.Interface as Interface

class Fun(commands.Cog):
    """Simple commands that induce Fun"""
    def __init__(self, bot):
        self.bot = bot
        self.delete = {} # -------
        self.pre_edit = {} #     |-- > Snipe command related dictionaries
        self.post_edit = {} # --=

    # Listeners for "snipe" command
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        self.delete[message.channel.id] =   (message.content, message.author, message.channel.id, message.created_at)

    @commands.Cog.listener()
    async def on_message_edit(self, pre_edit, post_edit):
        self.pre_edit[pre_edit.channel.id] =   (pre_edit.jump_url, pre_edit.content, pre_edit.author, pre_edit.channel.id, pre_edit.created_at)
        self.pre_edit[post_edit.channel.id] =   (post_edit.content, post_edit.author, post_edit.channel.id, post_edit.edited_at)

    # Mimics a user by sending a webhook as them.
    @commands.command(
        name = "as", 
        brief = "Send a Webhook")
    async def echo(self, ctx : commands.context, user : discord.Member, *, message):
        """Send a webhook message as the user you mentioned"""
        wbhk = await crucial.fetch_webhook(ctx.channel)
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
    async def delete(self, ctx : commands.context):
        """Get the details of the recently deleted message"""
        try:    
            message, author, channel, time    =   self.delete[ctx.channel.id]    
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
    async def edit(self, ctx : commands.context):
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
  
    @commands.command(
        name = "nitro",
        brief = "Gift Nitro")
    async def nitro(self, ctx : commands.context, *, user : discord.Member = None):
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
    async def pop(self, ctx, *, size : str = None):
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
   
async def setup(bot):
    await bot.add_cog(Fun(bot))