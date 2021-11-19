import discord
import asyncio
import json
from discord import VoiceRegion
from discord import user
from discord.ext import commands

def user_permissions(permissions):
    perm = []
    if permissions.administrator:
        perm.append('Admin')
        return['• Admin']
    
    if permissions.manage_guild:
        perm.append('• Manage Guild')

    if permissions.ban_members:
        perm.append('• Ban Guild Members')
    
    if permissions.kick_members:
        perm.append('• Kick Guild Members')

    if permissions.manage_channels:
        perm.append('• Manage Channels')

    if permissions.manage_emojis:
        perm.append('• Manage Emojis')
    
    if permissions.manage_permissions:
        perm.append('• Manage Member Permissions')
    
    if permissions.manage_roles:
        perm.append('• Manage Member Roles')
    
    if permissions.mention_everyone:
        perm.append('• Can ping @everyone')
    
    if permissions.mute_members:
        perm.append('• Can Mute Members')
    
    if permissions.deafen_members:
        perm.append('• Can Deafen Members')
    
    if permissions.view_audit_log:
        perm.append('• Can view the Audit Log')
    
    if permissions.manage_webhooks:
        perm.append('• Mange Webhooks')
    
    if permissions.create_instant_invite:
        perm.append('• Create Instant Invites')

    if len(perm) == 0:
        return None
    return perm

def user_badges(user, fetched_users):
    user_flags = user.public_flags
    flags = dict(user_flags)
    emoji_flags = ''
    emote = json.load(open('Program Files\Emotes.json'))

    if flags['staff'] is True:
        emoji_flags = f'{emoji_flags} {emote["User Info"]["staff"]}`Staff`'
        
    if flags['partner'] is True:
        emoji_flags = f'{emoji_flags} {emote["User Info"]["partner"]} `Partner`'
        
    if flags['hypesquad'] is True:
        emoji_flags = f'{emoji_flags} {emote["User Info"]["hype"]} `Hypesquad`'
        
    if flags['bug_hunter'] is True:
        emoji_flags = f'{emoji_flags} {emote["User Info"]["bug"]} `Bug Hunter`'
        
    if flags['hypesquad_bravery'] is True:
        emoji_flags = f'{emoji_flags} {emote["User Info"]["bravery"]} `Hypesquad Bravery`'
        
    if flags['hypesquad_brilliance'] is True:
        emoji_flags = f'{emoji_flags} {emote["User Info"]["brilliance"]} `Hypesquad Brilliance`'
        
    if flags['hypesquad_balance'] is True:
        emoji_flags = f'{emoji_flags} {emote["User Info"]["balance"]} `Hypesquad Balance`'
        
    if flags['early_supporter'] is True:
        emoji_flags = f'{emoji_flags} {emote["User Info"]["early"]} `Early Supporter`'
        
    if user.premium_since or user.avatar.is_animated():
        emoji_flags = f'{emoji_flags} {emote["User Info"]["nitro"]} `Nitro Subscriber`'
        
    if user.premium_since:
        emoji_flags = f'{emoji_flags} {emote["User Info"]["boost"]} `Server Booster`'
        
    if flags['verified_bot_developer'] is True:
        emoji_flags = f'{emoji_flags} {emote["User Info"]["dev"]} `Early Verified Bot Dev.`'
        
    if emoji_flags == '': emoji_flags = None
    
    return emoji_flags

def guild_region_emote(guild : discord.Guild):
    
    r = discord.VoiceRegion.us_central
    region = guild.region

    if region == VoiceRegion.amsterdam:
        return '🇳🇱'
    if region == VoiceRegion.brazil:
        return '🇧🇷'
    if region == VoiceRegion.dubai:
        return '🇦🇪'
    if region == VoiceRegion.eu_central:
        return '🇪🇺'
    if region == VoiceRegion.eu_west:
        return '🇪🇺'
    if region == VoiceRegion.europe:
        return '🇪🇺'
    if region == VoiceRegion.frankfurt:
        return '🇩🇪'
    if region == VoiceRegion.hongkong:
        return '🇭🇰'
    if region == VoiceRegion.india:
        return '🇮🇳'
    if region == VoiceRegion.japan:
        return '🇯🇵'
    if region == VoiceRegion.london:
        return '🇬🇧'
    if region == VoiceRegion.russia:
        return '🇷🇺'
    if region == VoiceRegion.singapore:
        return '🇸🇬'
    if region == VoiceRegion.southafrica:
        return '🇿🇦'
    if region == VoiceRegion.south_korea:
        return '🇰🇷'
    if region == VoiceRegion.sydney:
        return '🇦🇺'
    if region == VoiceRegion.us_central:
        return '🇺🇸'
    if region == VoiceRegion.us_east:
        return '🇺🇸'
    if region == VoiceRegion.us_south:
        return '🇺🇸'
    if region == VoiceRegion.us_west:
        return '🇺🇸'
    if region == VoiceRegion.vip_amsterdam:
        return '🇳🇱🌟'
    if region == VoiceRegion.vip_us_east:
        return '🇺🇸🌟'
    if region == VoiceRegion.vip_us_west:
        return '🇺🇸🌟'
    else:
        return ':x:'

def guild_region(guild : discord.Guild):
    
    R = discord.VoiceRegion.us_central
    region = guild.region

    if region == VoiceRegion.amsterdam:
        return 'Amsterdam'
    
    if region == VoiceRegion.brazil:
        return 'Brazil'
    
    if region == VoiceRegion.dubai:
        return 'Dubai'
    
    if region == VoiceRegion.eu_central:
        return 'EU - Central'
    
    if region == VoiceRegion.eu_west:
        return 'EU - West'
    
    if region == VoiceRegion.europe:
        return 'Europe'
    
    if region == VoiceRegion.frankfurt:
        return 'Frankfurt'
    
    if region == VoiceRegion.hongkong:
        return 'Hong Kong'
    
    if region == VoiceRegion.india:
        return 'India'
    
    if region == VoiceRegion.japan:
        return 'Japan'
    
    if region == VoiceRegion.london:
        return 'London'
    
    if region == VoiceRegion.russia:
        return 'Russia'
    
    if region == VoiceRegion.singapore:
        return 'Singapore'
    
    if region == VoiceRegion.southafrica:
        return 'South Africa'
    
    if region == VoiceRegion.south_korea:
        return 'South Korea'
    
    if region == VoiceRegion.sydney:
        return 'Sydney'
    
    if region == VoiceRegion.us_central:
        return 'US Central'
    
    if region == VoiceRegion.us_east:
        return 'US East'
    
    if region == VoiceRegion.us_south:
        return 'US South'
    
    if region == VoiceRegion.us_west:
        return 'US West'
    
    if region == VoiceRegion.vip_amsterdam:
        return 'VIP Amsterdam'
    
    if region == VoiceRegion.vip_us_east:
        return 'VIP US East'
    
    if region == VoiceRegion.vip_us_west:
        return 'VIP US West'
    
    else:
        return 'Unknown region'