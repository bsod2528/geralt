import os
import re
from typing import Dict, Union

import aiofiles
import discord

# Counts the total lines, taken from DuckBot by LeoCx1000


async def total_lines(path: str, filetype: str = ".py", skip_venv: bool = True):
    lines = 0
    for i in os.scandir(path):
        if i.is_file():
            if i.path.endswith(filetype):
                if skip_venv and re.search(r"(\\|/)?venv(\\|/)", i.path):
                    continue
                lines += len(
                    (
                        await (
                            await aiofiles.open(i.path, "r", encoding="utf-8")
                        ).read()
                    ).split("\n")
                )
        elif i.is_dir():
            lines += await total_lines(i.path, filetype)
    return lines


# Counts others [ classes and functions ]


async def misc(path: str, filetype: str = ".py", file_has: str = "def"):
    count_lines = 0
    for i in os.scandir(path):
        if i.is_file():
            if i.path.endswith(filetype):
                count_lines += len(
                    [
                        line
                        for line in (
                            await (
                                await aiofiles.open(i.path, "r", encoding="utf-8")
                            ).read()
                        ).split("\n")
                        if file_has in line
                    ]
                )
        elif i.is_dir():
            count_lines += await misc(i.path, filetype, file_has)
    return count_lines


# Taken from R.Danny Bot by Rapptz - Danny [ Github Profile Name ]
class Plural:
    def __init__(self, value):
        self.value = value

    def __format__(self, format_spec):
        v = self.value
        singular, sep, plural = format_spec.partition("|")
        plural = plural or f"{singular}s"
        if abs(v) != 1:
            return f"{v} {plural}"
        return f"{v} {singular}"


class TabulateData:
    def __init__(self):
        self._widths = []
        self._columns = []
        self._rows = []

    def columns(self, columns):
        self._columns = columns
        self._widths = [len(c) + 2 for c in columns]

    def add_rows(self, row):
        rows = [str(r) for r in row]
        self._rows.append(rows)
        for index, element in enumerate(rows):
            width = len(element) + 2
            if width > self._widths[index]:
                self._widths[index] = width

    def rows_added(self, rows):
        for row in rows:
            self.add_rows(row)

    def render(self):
        sep = "+".join("─" * w for w in self._widths)
        sep = f"+{sep}+"

        to_draw = [sep]

        def get_entry(d):
            elem = "│".join(f"{e:^{self._widths[i]}}" for i, e in enumerate(d))
            return f"│{elem}│"

        to_draw.append(get_entry(self._columns))
        to_draw.append(sep)

        for row in self._rows:
            to_draw.append(get_entry(row))

        to_draw.append(sep)
        return "\n".join(to_draw)


# Takes care of webhooks
class WebhookManager:
    def __init__(self) -> None:
        self.webhooks: Dict[int, discord.Webhook] = {}

    def __repr__(self) -> str:
        return "<Webhook Manager>"

    async def fetch_webhook(
        self, channel: Union[discord.TextChannel, discord.Thread]
    ) -> discord.Webhook:
        if isinstance(channel, discord.Thread):
            assert channel.parent and not isinstance(
                channel.parent, discord.ForumChannel
            )
            channel = channel.parent

        if channel.id not in self.webhooks:
            self.webhooks[channel.id] = await self.create_webhook(channel)

        return self.webhooks[channel.id]

    # Make a webhook if it"s own is not present.
    async def create_webhook(
        self, channel: Union[discord.TextChannel, discord.Thread]
    ) -> discord.Webhook:
        if isinstance(channel, discord.Thread):
            channel = channel.parent
        webhook_list = await channel.webhooks()
        if webhook_list:
            for hook in webhook_list:
                if hook.token:
                    return hook
        webhook = await channel.create_webhook(
            name="Geralt's Webhook", avatar=await channel.guild.me.display_avatar.read()
        )
        return webhook
