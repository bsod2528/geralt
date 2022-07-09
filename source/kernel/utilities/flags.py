import discord

# Has required flags for Server and User Info Commands
def user_perms(permissions):
    perms_list = []
    if permissions.administrator:
        perms_list.append("Admin")
        return["Admin"]
    
    if permissions.manage_guild:
        perms_list.append("Manage Guild")

    if permissions.ban_members:
        perms_list.append("Ban Guild Members")
    
    if permissions.kick_members:
        perms_list.append("Kick Guild Members")

    if permissions.manage_channels:
        perms_list.append("Manage Channels")

    if permissions.manage_emojis:
        perms_list.append("Manage Emojis")
    
    if permissions.manage_permissions:
        perms_list.append("Manage Member Permissions")
    
    if permissions.manage_roles:
        perms_list.append("Manage Member Roles")
    
    if permissions.mention_everyone:
        perms_list.append("Ping @everyone")
    
    if permissions.mute_members:
        perms_list.append("Mute Members")
    
    if permissions.deafen_members:
        perms_list.append("Deafen Members")
    
    if permissions.view_audit_log:
        perms_list.append("View the Audit Log")
    
    if permissions.manage_webhooks:
        perms_list.append("Mange Webhooks")
    
    if permissions.create_instant_invite:
        perms_list.append("Create Instant Invites")

    if len(perms_list) == 0:
        return None
    return perms_list

def user_badges(user: discord.User, fetch_user):
    user_flags = user.public_flags
    flags = dict(user_flags)
    flags_emote = ""

    if flags["staff"] is True:
        flags_emote = f"{flags_emote} <:DiscordStaff:905668211163406387> `Staff`"
        
    if flags["partner"] is True:
        flags_emote = f"{flags_emote} <a:DiscordPartner:905674460118540308> `Partner`"
        
    if flags["hypesquad"] is True:
        flags_emote  = f"{flags_emote} <a:WumpusHypesquad:905661121501990923> `Hypesquad`"
        
    if flags["bug_hunter"] is True:
        flags_emote  = f"{flags_emote} <:BugHunter:905668417372180540> `Bug Hunter`"
        
    if flags["hypesquad_bravery"] is True:
        flags_emote = f"{flags_emote} <:Bravery:905661473940979732> `Hypesquad Bravery`"
        
    if flags["hypesquad_brilliance"] is True:
        flags_emote = f"{flags_emote} <:Brilliance:905661426373373962> `Hypesquad Brilliance`"
        
    if flags["hypesquad_balance"] is True:
        flags_emote = f"{flags_emote} <:Balance:932965710337019924> `Hypesquad Balance`"
        
    if flags["early_supporter"] is True:
        flags_emote = f"{flags_emote} <:EarlySupporter:905674700955467806> `Early Supporter`"
        
    if user.premium_since:
        flags_emote = f"{flags_emote} <:WumpusNitro:905674712590454834> `Nitro Subscriber`"
        
    if user.premium_since:
        flags_emote = f"{flags_emote} <a:Nitro:905661661191479326> `Server Booster`"
        
    if flags["verified_bot_developer"] is True:
        flags_emote = f"{flags_emote} <:VerifiedDev:905668791831265290> `Early Verified Bot Dev.`"
        
    if flags_emote == "" : flags_emote = None
    
    return flags_emote