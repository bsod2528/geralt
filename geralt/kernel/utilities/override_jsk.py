import contextlib
from typing import Union

import discord
import jishaku.exception_handling
import jishaku.paginators
from jishaku.meta import __version__

# This method is taken from stella_bot made by InterStella0 [ Github ID ]


async def attempt_add_reaction(msg: discord.Message, reaction: Union[str, discord.Emoji]):
    reacts = {
        "\N{WHITE HEAVY CHECK MARK}": "<a:Verify:905748402871095336>",
        "\N{BLACK RIGHT-POINTING TRIANGLE}": "<:Join:932976724235395072>",
        "\N{HEAVY EXCLAMATION MARK SYMBOL}": "<a:Nope:988845795920990279>",
        "\N{DOUBLE EXCLAMATION MARK}": "<:NanoCross:965845144307912754>",
        "\N{ALARM CLOCK}": "<a:Time:988848156500451348>"
    }
    react = reacts[reaction] if reaction in reacts else reaction
    with contextlib.suppress(discord.HTTPException):
        return await msg.add_reaction(react)

jishaku.exception_handling.attempt_add_reaction = attempt_add_reaction
