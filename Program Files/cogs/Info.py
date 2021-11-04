import json
import discord 
import random
import asyncio
import datetime
from discord.enums import VerificationLevel
from discord.utils import resolve_annotation
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

    @commands.command(
        name = 'guildinfo',
        aliases = ['gi'],
        help = f'```ini\n[ Syntax : .gguildinfo [ Guild ID ] ]\n```\n>>> **USE :** Get Information regarding any Guild\n**AKA :** `.ggi`',
        brief = 'Sends Guild Information')
    async def guildinfo(self, ctx, ID : int = None):
        if ID:
            guild = self.bot.get_guild(id)
            if not guild:
                return await ctx.reply(f'Bruh!, I couldnt find any guild with what you provided! Enter a proper guild IDs', mention_author = False)
        else:
            guild = ctx.guild
        if str(guild.verification_level).lower() == 'Low':
            VerificationLevel = 'Level 1 • Low'
            
        elif str(guild.verification_level).lower() == 'Medium':
            VerificationLevel = 'Level 2 • Medium'
            
        elif str(guild.verification_level).lower() == 'High':
            VerificationLevel = 'Level 3 • High'
            
        elif str(guild.verification_level).lower() == 'Extreme':
            VerificationLevel = 'Level 4 • Extreme'
            
        else:
            VerificationLevel = 'No Verification Requiried'
        member_status   =   [len(list(filter(lambda m: str(m.status) == 'online', guild.members))),
                            len(list(filter(lambda m: str(m.status) == 'idle', guild.members))),
                            len(list(filter(lambda m: str(m.status) == 'dnd', guild.members))),
                            len(list(filter(lambda m: str(m.status) == 'offline', guild.members)))]

        guild_info = discord.Embed(
            title = f'{guild}',
            color = self.color)
        guild_info.add_field(
            name = 'Guild Analytics :',
            value = f'<:replygoin:897151741320122458> • **<a:Owner:905750348457738291> Owner :** {guild.owner.mention}\n'
                    f'<:replygoin:897151741320122458> • **<a:HappyBirthday:905754435379163176> Created On :**( {discord.utils.format_dt(guild.created_at)} )\n'
                    f'<:replygoin:897151741320122458> • **<a:Info:905750331789561856> ID :** ` {guild.id} `\n'
                    f'<:reply:897151692737486949> • **<a:Verify:905748402871095336> Verification :** {guild.verification_level}\n')
        guild_info.add_field(
            name = 'Guild Members :',
            value = f'<:replygoin:897151741320122458> • **<a:HumanBro:905748764432662549> No. of Humans :** {len(list(filter(lambda m: m.bot is False, guild.members)))}\n'
                    f'<:replygoin:897151741320122458> • **<a:BotLurk:905749164355379241> No. of Bots :** {len(list(filter(lambda m: m.bot, guild.members)))}\n'
                    f'<:replygoin:897151741320122458> • **<a:Users:905749451350638652> Total :** {ctx.guild.member_count}\n'
                    f'<:reply:897151692737486949> • **Region :** {InfoHelp.guild_region(guild)} {InfoHelp.guild_region_emote(guild)}',
            inline = False)
        guild_info.add_field(
            name = 'Channels Present :',
            value = f'<:replygoin:897151741320122458> • **<:Channel:905674680436944906> Text Channels :** {len(guild.text_channels)}\n'
                    f'<:replygoin:897151741320122458> • **<:StageChannel:905674422839554108> Stage Channels :** {len(guild.stage_channels)}\n'
                    f'<:replygoin:897151741320122458> • **<a:Thread:905750997706629130> Thread Channels :** {len(guild.threads)}\n'
                    f'<:reply:897151692737486949> • **<:Voice:905746719034187796> Voice Channels :** {len(guild.voice_channels)}\n',
            inline = False)
        guild_info.add_field(
            name = 'Members Status :',
            value = f'<:replygoin:897151741320122458> • **<:Online:905757053119766528> Online :** {member_status[0]} \n'
                    f'<:replygoin:897151741320122458> • **<:Idle:905757063064453130> Idle :** {member_status[1]}\n'
                    f'<:replygoin:897151741320122458> • **<:DnD:905759353141874709> Do Not Disturb :** {member_status[2]}\n'
                    f'<:reply:897151692737486949> • **<:Offline:905757032521551892> Offline :** {member_status[3]}\n',
            inline = True)
        guild_info.timestamp = self.timestamp
        guild_info.set_footer(
            text = f'Invoked by {ctx.author}',
            icon_url = ctx.author.avatar.url)
        guild_info.set_thumbnail(url = guild.icon)
        await ctx.reply(embed = guild_info, mention_author = False)

def setup(bot):
    bot.add_cog(Info(bot))