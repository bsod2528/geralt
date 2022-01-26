import disnake

from disnake.ext import commands

import Source.Kernel.Utilities.Crucial as CRUCIAL

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot            =   bot
        self.DELETE         =   {}  # ---
        self.PRE_EDIT       =   {}  #   |-- > Snipe command related dictionaries
        self.POST_EDIT      =   {}  # --=

    # Listeners for "snipe" command
    @commands.Cog.listener()
    async def on_message_delete(self, MESSAGE):
        self.DELETE[MESSAGE.channel.id] =   (MESSAGE.content, MESSAGE.author, MESSAGE.channel.id, MESSAGE.created_at)

    @commands.Cog.listener()
    async def on_message_edit(self, PRE_EDIT, POST_EDIT):
        self.PRE_EDIT[PRE_EDIT.channel.id] =   (PRE_EDIT.content, PRE_EDIT.author, PRE_EDIT.channel.id, PRE_EDIT.created_at)
        self.POST_EDIT[POST_EDIT.channel.id] =   (POST_EDIT.content, POST_EDIT.author, POST_EDIT.channel.id, POST_EDIT.edited_at)

    # Mimics a user by sending a webhook as them.
    @commands.command(
        name    =   "as", 
            brief   =   "Send a Webhook",
        help    =   "Send a webhook message as the user you mentioned")
    async def echo(self, ctx, USER : disnake.Member, *, MESSAGE):
        WBHK = await CRUCIAL.FETCH_WEBHOOK(ctx.channel)
        thread = disnake.utils.MISSING
        if isinstance(ctx.channel, disnake.Thread):
            thread = ctx.channel
        await WBHK.send(
            MESSAGE, 
            avatar_url  =   USER.display_avatar.url, 
            username    =   USER.display_name, 
           thread      =   thread)
        await ctx.message.delete(delay = 0)

    # Snipe command as a group
    @commands.group(
        name    =   "snipe",
        aliases =   ["s"],
        brief   =   "Get edited / deleted messages")
    async def snipe(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)
    
    # Snipes for deleted messages
    @snipe.command(
        name    =   "delete",
        aliases =   ["del", "d"],
        brief   =   "Snipe Deleted Messages",
        help    =   "Get the details of the recently deleted message")
    async def delete(self, ctx):
        try:    
            MESSAGE, AUTHOR, CHANNEL, TIME    =   self.DELETE[ctx.channel.id]    
            DELETE_EMB   =   disnake.Embed(
                title   =   "Sniped Deleted Message",
                description =   f"**<:ReplyContinued:930634770004725821> - Message Author :** {AUTHOR.mention} (`{AUTHOR.id}`)\n**<:ReplyContinued:930634770004725821> - In Channel :** <#{CHANNEL}> (`{CHANNEL}`)\n**<:Reply:930634822865547294> - Message Created At :** {self.bot.DT(TIME)}",
                colour  =   self.bot.colour)
            DELETE_EMB.add_field(
                name    =   "Message Content",
                value   =   f"```json\n{MESSAGE}\n```")
            DELETE_EMB.timestamp    =   self.bot.Timestamp
            await ctx.reply(embed = DELETE_EMB, allowed_mentions = self.bot.Mention)
        except Exception as e:
            await ctx.send(f"No snipe : {e}")

    # Snipes for edited messages
    @snipe.command(
        name    =   "edit",
        aliases =   ["ed", "e"],
        brief   =   "Snipe Edited Messages",
        help    =   "Get the details of the recently edited message")
    async def edit(self, ctx):
        try:    
            MESSAGE, AUTHOR, CHANNEL, PRE_TIME          =   self.PRE_EDIT[ctx.channel.id]    
            POST_MESSAGE, AUTHOR, CHANNEL, POST_TIME    =   self.POST_EDIT[ctx.channel.id]    
            EDIT_EMB   =   disnake.Embed(
                title   =   "Sniped Edited Message",
                description =   f"**<:ReplyContinued:930634770004725821> - Message Author :** {AUTHOR.mention} (`{AUTHOR.id}`)\n**<:ReplyContinued:930634770004725821> - In Channel :** <#{CHANNEL}> (`{CHANNEL}`)\n**<:Reply:930634822865547294> - Message Sent At :** {self.bot.DT(PRE_TIME)}",
                colour  =   self.bot.colour)
            EDIT_EMB.add_field(
                name    =   "Before Edit",
                value   =   f"```json\n{MESSAGE}\n```")
            EDIT_EMB.add_field(
                name    =   "After Edit",
                value   =   f"**<:Reply:930634822865547294> - Message Edited at :** {self.bot.DT(POST_TIME)}\n```json\n{POST_MESSAGE}\n```",
                inline  =   False)
            await ctx.reply(embed = EDIT_EMB, allowed_mentions = self.bot.Mention)
        except Exception as e:
            await ctx.send(f"No snipe : {e}")

def setup(bot):
    bot.add_cog(Fun(bot))