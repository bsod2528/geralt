import discord

from discord.ext.commands import Group

from ..subclasses.bot import Geralt
from ..subclasses.embed import BaseEmbed
from ..subclasses.context import GeraltContext

class HelpMenu(discord.ui.Select):
    def __init__(self, mapping, help, cog_list):
        options = [discord.SelectOption(label = cog.qualified_name, description = cog.description, emoji = cog.emote) for cog in cog_list]
        super().__init__(
            options = options,
            min_values = 1,
            max_values = 1,
            placeholder = "Choose a cog")
        self.bot: Geralt = help.context.bot 
        self.ctx: GeraltContext = help.context
        self.help = help
        self.mapping = mapping

    async def callback(self, interaction: discord.Interaction):
        for cog, commands in self.mapping.items():
            emote = getattr(cog, "emote", None)
            if cog is not None:
                if self.values[0] == cog.qualified_name:
                    callback_emb = BaseEmbed(
                        title = f"{cog.qualified_name} Commands",
                        description = f"{cog.description} {emote}" if cog and cog.description else "`. . .`",
                        colour = self.bot.colour)
                    filtered_commands = await self.help.filter_commands(commands, sort = True)
                    for commands in filtered_commands:
                        callback_emb.add_field(
                                name = f"<:Join:932976724235395072> {commands.qualified_name}",
                                value = f"> ` ─ ` {commands.short_doc} {'<:G:915108274263703553>' if isinstance(commands, Group) else ' '}" or "Yet to be documented",
                                inline = False)
                        callback_emb.set_thumbnail(url = self.ctx.me.display_avatar)
                        callback_emb.set_footer(text = self.help.footer(), icon_url = self.ctx.author.display_avatar)
        try:
            await interaction.response.edit_message(embed = callback_emb)
        except discord.errors.NotFound:
            return

class HelpView(discord.ui.View):
    def __init__(self, mapping, help, cog_list):
        super().__init__(timeout = 180)
        self.help = help
        self.mapping = mapping
        self.add_item(HelpMenu(mapping, help, cog_list))
    
    def footer(self):
        return f"Run {self.help.context.clean_prefix}help [cog | command] for more info."

    @discord.ui.button(label = "Home", style = discord.ButtonStyle.grey, emoji = "\U0001f3d8", row = 2)
    async def home(self, interaction: discord.Interaction, button: discord.ui.Button):
        help_emb = BaseEmbed(
            title = f"\U00002728 {self.help.context.author}'s Help",
            description = f"────\nHi! I am [**Geralt**](https://github.com/BSOD2528/Geralt) and open source Discord Bot made for fun.\n────",
            colour = self.help.context.bot.colour)
        
        for cog, commands in self.mapping.items():
            filtered_cmds = await self.help.filter_commands(commands, sort = True)
            if filtered_cmds:
                if cog is None:
                    continue
                emote = getattr(cog, "emote", None)
                help_emb.add_field(
                    name = f"{emote} {cog.qualified_name}", 
                    value = f"<:Join:932976724235395072> `{self.help.context.clean_prefix}help {cog.qualified_name}`",
                    inline = True)
                help_emb.set_thumbnail(url = self.help.context.me.display_avatar)
                help_emb.set_footer(text = self.footer(), icon_url = self.help.context.author.display_avatar)
        try:
            await interaction.response.edit_message(embed = help_emb, view = self)
        except discord.errors.NotFound:
            pass

    @discord.ui.button(label = "Updates", style = discord.ButtonStyle.grey, emoji = "\U0001f4dc", row = 2)
    async def updates(self, interaction: discord.Interaction, button: discord.ui.Button):
        updates_emb = BaseEmbed(
            title = "Latest Updates",
            description = f"The following points list down the latest updates made as of <t:1655651880:D> (<t:1655651880:R>)",
            colour = self.help.context.bot.colour)
        updates_emb.add_field(
            name = "Updates :",
            value = f">>> `1).` <t:1655957078:R> ─ <a:Info:905750331789561856> Added `{self.help.context.clean_prefix}source`\n" \
                    f"`2).` <t:1655651880:R> ─ <:Ticket:987172295762149446> Added Ticket system. Enable it by running `{self.help.context.clean_prefix}ticket`\n" \
                    f"`3).` <t:1655224433:R> ─ <a:Byee:915568796536815616> Added `{self.help.context.clean_prefix}afk`.\n" \
                    f"`4).` <t:1654180236:R> ─ <a:Owner:905750348457738291> Developers can now blacklist users from using the bot using `{self.help.context.clean_prefix}blacklist`. \n" \
                    f"`5).` <t:1653417000:R> ─ <a:WumpusHypesquad:905661121501990923> Added `[--size]` argument to `{self.help.context.clean_prefix}pop` \n")
        updates_emb.set_footer(text = self.help.footer(), icon_url = self.help.context.me.display_avatar)
        try:
            await interaction.response.edit_message(embed = updates_emb, view = self)
        except discord.errors.NotFound:
            return

    @discord.ui.button(label = "Arg-Usage", style = discord.ButtonStyle.grey, emoji = "<a:Verify:905748402871095336>", row = 2)
    async def arg_usage(self, interaction: discord.Interaction, button: discord.ui.Button):
        arg_usage_emb = BaseEmbed(
            title = ":scroll: Argument Usage",
            description = f"The following showcase how you are supposed to pass in arguments for invoking commands using `{self.help.context.clean_prefix}`. " \
                          f"An \"**argument**\" is a value that is passed into the command in order to successfully invoke the command.\n" \
                          f"\n> <:Join:932976724235395072> `<argument>` : Compulsory Argument\n> <:Join:932976724235395072> `[argument]` : Optional Argument\n" \
                          f"> <:Join:932976724235395072> `[argument A | argument B]` : Either Argument A or B\n> <:Join:932976724235395072> `[argument ...]` : Multiple values are to be passed\n" \
                          f"> <:Join:932976724235395072> `[--flags]` : These are arguments passed in via using flags. `--` has to be used before passing in the value.\n\n" \
                          f"When passing in arguemnts, ensure not to type `<> / []`. Those symbols are used to represent the type of argument they are.",
            colour = self.help.context.bot.colour)
        arg_usage_emb.set_footer(text = self.help.footer(), icon_url = self.help.context.me.display_avatar)
        try:
            await interaction.response.edit_message(embed = arg_usage_emb, view = self)
        except discord.errors.NotFound:
            return
    
    @discord.ui.button(label = "Delete", style = discord.ButtonStyle.red, emoji = "<a:Trash:906004182463569961>", row = 2)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()
    
    async def interaction_check(self, interaction : discord.Interaction) -> bool:
        pain = f"{interaction.user.mention} ─ This view can't be handled by you at the moment <:Bonked:934033408106057738>, it is meant for {self.help.context.author.mention}\nInvoke for youself by running `{self.help.context.clean_prefix}{self.help.context.command}` for the `{self.help.context.command}` command <:SarahPray:920484222421045258>"
        if interaction.user == self.help.context.author:
            return True
        else:
            await interaction.response.send_message(content = f"{pain}", ephemeral = True)

class Delete(discord.ui.View):
    def __init__(self, help):
        super().__init__()
        self.help = help

    @discord.ui.button(label = "Delete", style = discord.ButtonStyle.red, emoji = "<a:Trash:906004182463569961>")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()

    async def interaction_check(self, interaction : discord.Interaction) -> bool:
        pain = f"{interaction.user.mention} ─ This view can't be handled by you at the moment <:Bonked:934033408106057738>, it is meant for {self.help.context.author.mention}\nInvoke for youself by running `{self.help.context.clean_prefix}{self.help.context.command}` for the `{self.help.context.command}` command <:SarahPray:920484222421045258>"
        if interaction.user == self.help.context.author:
            return True
        else:
            await interaction.response.send_message(content = f"{pain}", ephemeral = True)