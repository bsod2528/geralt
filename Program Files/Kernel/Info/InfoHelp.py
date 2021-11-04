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
        return['• `Admin`']
    
    if permissions.manage_guild:
        perm.append('• `Manage Guild`')

    if permissions.ban_members:
        perm.append('• `Ban Guild Members`')
    
    if permissions.kick_members:
        perm.append('• `Kick Guiild Members`')

    if permissions.manage_channels:
        perm.append('• `Manage Channels`')

    if permissions.manage_emojis:
        perm.append('• `Manage Emojis`')
    
    if permissions.manage_permissions:
        perm.append('• `Manage Member Permissions`')
    
    if permissions.manage_roles:
        perm.append('• `Manage Member Roles`')
    
    if permissions.mention_everyone:
        perm.append('• `Can <@everyone>`')
    
    if permissions.mute_members:
        perm.append('• `Can Mute Members`')
    
    if permissions.deafen_members:
        perm.append('• `Can Deafen Members`')
    
    if permissions.view_audit_log:
        perm.append('• `Can view the Audit Log`')
    
    if permissions.manage_webhooks:
        perm.append('• `Mange Webhooks`')
    
    if permissions.create_instant_invite:
        perm.append('• `Create Instant Invites`')

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