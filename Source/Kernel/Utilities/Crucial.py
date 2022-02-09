import os
import json
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

# Make a webhook if it's own is not present.
async def FETCH_WEBHOOK(channel) -> disnake.Webhook:
    if isinstance(channel, disnake.Thread):
        channel = channel.parent
    webhook_list = await channel.webhooks()
    if webhook_list:
        for HOOK in webhook_list:
            if HOOK.token:
                return HOOK
    WEBHOOK = await channel.create_webhook(
        name    =   "Geralt Webhook", 
        avatar  =   await channel.guild.me.display_avatar.read())
    return WEBHOOK

# Taken from R.Danny Bot by Rapptz - Danny [ Github Profile Name ]
class Plural:
    def __init__(self, value):
        self.value = value
    def __format__(self, format_spec):
        v = self.value
        singular, sep, plural = format_spec.partition('|')
        plural = plural or f'{singular}s'
        if abs(v) != 1:
            return f'{v} {plural}'
        return f'{v} {singular}'

class TabulateData:
    def __init__(self):
        self._widths    =   []
        self._columns   =   []
        self._rows      =   []

    def columns(self, columns):
        self._columns = columns
        self._widths = [len(c) + 2 for c in columns]

    def row_add(self, row):
        rows    =   [str(r) for r in row]
        self._rows.append(rows)
        for index, element in enumerate(rows):
            width = len(element) + 2
            if width > self._widths[index]:
                self._widths[index] = width

    def rows_added(self, rows):
        for row in rows:
            self.row_add(row)

    def render(self):
        sep =   "+".join("-"* w for w in self._widths)
        sep =   f"+{sep}+"
        
        to_draw =   [sep]

        def get_entry(d):
            elem    =   "|".join(f"{e:^{self._widths[i]}}" for i, e in enumerate(d))
            return f"|{elem}|"

        to_draw.append(get_entry(self._columns))
        to_draw.append(sep)

        for row in self._rows:
            to_draw.append(get_entry(row))

        to_draw.append(sep)
        return "\n".join(to_draw)