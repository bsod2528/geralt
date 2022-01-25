import os
import json
import time
import asyncio
import asyncpg
import disnake
import aiofiles

EMOTE   =   json.load(open(r"Source\Kernel\Utilities\Emote.json"))

# Counts the total lines
async def TOTAL_LINES(Path : str, FileType : str = ".py"):
    Lines = 0
    for i in os.scandir(Path):
        if i.is_file():
            if i.path.endswith(FileType):
                Lines += len((await (await aiofiles.open(i.path, 'r')).read()).split("\n"))
        elif i.is_dir():
            Lines += await TOTAL_LINES(i.path, FileType)
    return Lines

# Counts others [ classes and functions ]
async def MISC(Path : str, FileType: str = '.py', File_Has: str = 'def'):
    Count_Lines = 0
    for i in os.scandir(Path):
        if i.is_file():
            if i.path.endswith(FileType):
                Count_Lines += len([line for line in (await (await aiofiles.open(i.path, 'r')).read()).split("\n") if
                                   File_Has in line])
        elif i.is_dir():
            Count_Lines += await MISC(i.path, FileType, File_Has)
    return Count_Lines

async def FETCH_WEBHOOK(channel) -> disnake.Webhook:
    if isinstance(channel, disnake.Thread):
        channel = channel.parent
    webhook_list = await channel.webhooks()
    if webhook_list:
        for hook in webhook_list:
            if hook.token:
                return hook
    hook = await channel.create_webhook(
        name    =   "Geralt Webhook", 
        avatar  =   await channel.guild.me.display_avatar.read())
    return hook


# Database related queries
class DB_FUNCS:
    def __init__(self):
    
        async def EXECUTE(self, *ARGS, **KWARGS):
            """Execute SQL query"""
            QUERY   =   await asyncpg.pool.Pool.execute(*ARGS, **KWARGS)
            return QUERY
        
        async def EXECUTE_MANY(self, *ARGS, **KWARGS):
            """Execute multiple SQL queries"""
            QUERY   =   await asyncpg.pool.Pool.executemany(*ARGS, **KWARGS)
            return QUERY
        
        async def FETCH(self, *ARGS, **KWARGS):
            """Fetches data from table"""
            QUERY   =   await asyncpg.pool.Pool.fetch(*ARGS, **KWARGS)
            return QUERY

        async def FETCH_ROW(self, *ARGS, **KWARGS):
            """Fetches data from row"""
            QUERY   =   await asyncpg.pool.Pool.fetchrow(*ARGS, **KWARGS)
            return QUERY
        
        async def FETCH_VALUE(self, *ARGS, **KWARGS):
            """Fetches data from a given value"""
            QUERY   =   await asyncpg.pool.Pool.fetchval(*ARGS, **KWARGS)
            return QUERY