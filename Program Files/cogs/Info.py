import json
import discord 
import random
import asyncio
import datetime
import Kernel.Info.InfoHelp as InfoHelp
from discord import permissions
from discord.ext import commands

class Info(commands.Cog):
    
    """Get information regarding server members"""

    def __init__(self, bot):
        self.bot = bot
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)
        self.color = 0x2F3136
        self.emote = json.load(open('Program Files\Emotes.json'))
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)

    @commands.command(
        name = 'avatar',
        aliases = ['pfp'],
        help = f'```ini\n[ Syntax : .gavatar [member mention/id] ]\n```\n>>> **USE :** Gets the Avatar of a user or you!\n**AKA :** `.gpfp`',
        brief = 'See other members pfps enlarged')
    async def avatar(self, ctx, *, user : discord.Member = None):
        emb = discord.Embed(
            color = self.color)
        user = user or ctx.author
        avatar = user.display_avatar.with_static_format('png')
        emb.set_author(
            name = f'PFP of - {str(user)}', 
            url = avatar)
        emb.set_image(url = avatar)
        emb.timestamp = self.timestamp
        await ctx.reply(embed = emb, mention_author = False)

    @commands.command(
        name = 'userinfo',
        aliases = ['ui', 'user'],
        help = f'```ini\n[ Syntax : .guserinfo [ <member>/<user-id> ]\n```\n>>> **USE :** Get basic information about a user!\n **AKA :** `.gui` `.guser`',
        brief = 'Get user info')
    async def userinfo(self, ctx, *, user : discord.Member = None):
        user = user or ctx.author
        roles = ''
        for role in user.roles:
            if role is ctx.guild.default_role: continue
            roles = f'{roles} {role.mention}'
        if roles != '':
            roles = f'{roles}'
        fetched_user = await ctx.bot.fetch_user(user.id)
        permission = InfoHelp.user_permissions(user.guild_permissions)
        if permission:
            perms = f'{" | ".join(permission)}'
        else:
            perms = ''

        user_info = discord.Embed(
            title = f'{user.name} - {user}',
            color = self.color)
        user_info.add_field(
            name = 'Acc. Created On :',
            value = f'{discord.utils.format_dt(user.created_at)}')
        user_info.add_field(
            name = 'Joined Guild :',
            value = f'{discord.utils.format_dt(user.joined_at)}')
        user_info.add_field(
            name = 'Top Roles :',
            value = f'• {user.top_role.mention}',
            inline = False)
        user_info.add_field(
            name = 'All Roles :',
            value = f'• {roles}',
            inline = True)
        user_info.add_field(
            name = 'Perms Alloted :',
            value = f'{perms}',
            inline = False)
        user_info.add_field(
            name = 'Badges Present :',
            value = f'• {InfoHelp.user_badges(user = user, fetched_users = fetched_user) if InfoHelp.user_badges(user = user, fetched_users = fetched_user) else "`No Badges Present`"}',
            inline = False)
        user_info.timestamp = self.timestamp
        user_info.set_footer(
            text = f'ID : {user.id}')
        user_info.set_thumbnail(
            url = user.display_avatar.url)       
        await ctx.reply(embed = user_info, mention_author = False)

def setup(bot):
    bot.add_cog(Info(bot))