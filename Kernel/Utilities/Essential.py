import os
import time
import asyncio
import asyncpg

async def TOTAL_LINES(Path : str, FileType : str = ".py"):
    Lines = 0
    for L in os.scandir(Path):
        if L.is_file():
            if L.path.endswith(".py"):
               # Lines += len((await (await aiofiles.open(L.Path, 'r')).read()).split("\n"))
            #elif L.is_dir():
                Lines += await TOTAL_LINES(L.Path, FileType)
    return Lines

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

