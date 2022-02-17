import json
import discord

from discord import VoiceRegion as VR

EMOTE   =   json.load(open(r"Source\Kernel\Utilities\Emote.json"))

# Has required flags for Server and User Info Commands
def USER_PERMS(PERMISSIONS):
    PERMS_DICT  =   []
    if PERMISSIONS.administrator:
        PERMS_DICT.append("Admin")
        return["Admin"]
    
    if PERMISSIONS.manage_guild:
        PERMS_DICT.append("Manage Guild")

    if PERMISSIONS.ban_members:
        PERMS_DICT.append("Ban Guild Members")
    
    if PERMISSIONS.kick_members:
        PERMS_DICT.append("Kick Guild Members")

    if PERMISSIONS.manage_channels:
        PERMS_DICT.append("Manage Channels")

    if PERMISSIONS.manage_emojis:
        PERMS_DICT.append("Manage Emojis")
    
    if PERMISSIONS.manage_permissions:
        PERMS_DICT.append("Manage Member Permissions")
    
    if PERMISSIONS.manage_roles:
        PERMS_DICT.append("Manage Member Roles")
    
    if PERMISSIONS.mention_everyone:
        PERMS_DICT.append("Ping @everyone")
    
    if PERMISSIONS.mute_members:
        PERMS_DICT.append("Mute Members")
    
    if PERMISSIONS.deafen_members:
        PERMS_DICT.append("Deafen Members")
    
    if PERMISSIONS.view_audit_log:
        PERMS_DICT.append("View the Audit Log")
    
    if PERMISSIONS.manage_webhooks:
        PERMS_DICT.append("Mange Webhooks")
    
    if PERMISSIONS.create_instant_invite:
        PERMS_DICT.append("Create Instant Invites")

    if len(PERMS_DICT) == 0:
        return None
    return PERMS_DICT

def USER_BADGES(USER, FETCH_USER):
    USER_FLAGS  =   USER.public_flags
    FLAGS       =   dict(USER_FLAGS)
    FLAG_EMOTE  =   ""

    if FLAGS["staff"] is True:
        FLAG_EMOTE  =   f"{FLAG_EMOTE} {EMOTE['Discord']['Staff']} `Staff`"
        
    if FLAGS["partner"] is True:
        FLAG_EMOTE  =   f"{FLAG_EMOTE} {EMOTE['Discord']['Partner']} `Partner`"
        
    if FLAGS["hypesquad"] is True:
        FLAG_EMOTE  =   f"{FLAG_EMOTE} {EMOTE['Discord']['Hypesquad']} `Hypesquad`"
        
    if FLAGS["bug_hunter"] is True:
        FLAG_EMOTE  =   f"{FLAG_EMOTE} {EMOTE['Discord']['Bug']} `Bug Hunter`"
        
    if FLAGS["hypesquad_bravery"] is True:
        FLAG_EMOTE  =   f"{FLAG_EMOTE} {EMOTE['Discord']['Bravery']} `Hypesquad Bravery`"
        
    if FLAGS["hypesquad_brilliance"] is True:
        FLAG_EMOTE  =   f"{FLAG_EMOTE} {EMOTE['Discord']['Brilliance']} `Hypesquad Brilliance`"
        
    if FLAGS["hypesquad_balance"] is True:
        FLAG_EMOTE  =   f"{FLAG_EMOTE} {EMOTE['Discord']['Balance']} `Hypesquad Balance`"
        
    if FLAGS["early_supporter"] is True:
        FLAG_EMOTE  =   f"{FLAG_EMOTE} {EMOTE['Discord']['Early']} `Early Supporter`"
        
    if USER.premium_since or USER.avatar.is_animated():
        FLAG_EMOTE  =   f"{FLAG_EMOTE} {EMOTE['Discord']['Nitro']} `Nitro Subscriber`"
        
    if USER.premium_since:
        FLAG_EMOTE  =   f"{FLAG_EMOTE} {EMOTE['Discord']['Booster']} `Server Booster`"
        
    if FLAGS["verified_bot_developer"] is True:
        FLAG_EMOTE  =   f"{FLAG_EMOTE} {EMOTE['Discord']['Dev']} `Early Verified Bot Dev.`"
        
    if FLAG_EMOTE   ==  "" : FLAG_EMOTE = None
    
    return FLAG_EMOTE

def GUILD_EMOTE(GUILD : discord.Guild):
    REGION  =   GUILD.region

    if REGION   ==  VR.amsterdam:
        return "🇳🇱"
    if REGION   ==  VR.brazil:
        return "🇧🇷"
    if REGION   ==  VR.dubai:
        return "🇦🇪"
    if REGION   ==  VR.eu_central:
        return "🇪🇺"
    if REGION   ==  VR.eu_west:
        return "🇪🇺"
    if REGION   ==  VR.europe:
        return "🇪🇺"
    if REGION   ==  VR.frankfurt:
        return "🇩🇪"
    if REGION   ==  VR.hongkong:
        return "🇭🇰"
    if REGION   ==  VR.india:
        return "🇮🇳"
    if REGION   ==  VR.japan:
        return "🇯🇵"
    if REGION   ==  VR.london:
        return "🇬🇧"
    if REGION   ==  VR.russia:
        return "🇷🇺"
    if REGION   ==  VR.singapore:
        return "🇸🇬"
    if REGION   ==  VR.southafrica:
        return "🇿🇦"
    if REGION   ==  VR.south_korea:
        return "🇰🇷"
    if REGION   ==  VR.sydney:
        return "🇦🇺"
    if REGION   ==  VR.us_central:
        return "🇺🇸"
    if REGION   ==  VR.us_east:
        return "🇺🇸"
    if REGION   ==  VR.us_south:
        return "🇺🇸"
    if REGION   ==  VR.us_west:
        return "🇺🇸"
    if REGION   ==  VR.vip_amsterdam:
        return "🇳🇱🌟"
    if REGION   ==  VR.vip_us_east:
        return "🇺🇸🌟"
    if REGION   ==  VR.vip_us_west:
        return "🇺🇸🌟"
    else:
        return "<:WinUncheck:898572376147623956>"

def GUILD_REGION(GUILD : discord.Guild):
    REGION  =   GUILD.region

    if REGION   ==  VR.amsterdam:
        return "Amsterdam"
    
    if REGION   ==  VR.brazil:
        return "Brazil"
    
    if REGION   ==  VR.dubai:
        return "Dubai"
    
    if REGION   ==  VR.eu_central:
        return "EU - Central"
    
    if REGION   ==  VR.eu_west:
        return "EU - West"
    
    if REGION   ==  VR.europe:
        return "Europe"
    
    if REGION   ==  VR.frankfurt:
        return "Frankfurt"
    
    if REGION   ==  VR.hongkong:
        return "Hong Kong"
    
    if REGION   ==  VR.india:
        return "India"
    
    if REGION   ==  VR.japan:
        return "Japan"
    
    if REGION   ==  VR.london:
        return "London"
    
    if REGION   ==  VR.russia:
        return "Russia"
    
    if REGION   ==  VR.singapore:
        return "Singapore"
    
    if REGION   ==  VR.southafrica:
        return "South Africa"
    
    if REGION   ==  VR.south_korea:
        return "South Korea"
    
    if REGION   ==  VR.sydney:
        return "Sydney"
    
    if REGION   ==  VR.us_central:
        return "US Central"
    
    if REGION   ==  VR.us_east:
        return "US East"
    
    if REGION   ==  VR.us_south:
        return "US South"
    
    if REGION   ==  VR.us_west:
        return "US West"
    
    if REGION   ==  VR.vip_amsterdam:
        return "VIP Amsterdam"
    
    if REGION   ==  VR.vip_us_east:
        return "VIP US East"
    
    if REGION   ==  VR.vip_us_west:
        return "VIP US West"
    
    else:
        return "Either Unknown or Depricated Region"