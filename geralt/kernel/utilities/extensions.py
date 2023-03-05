from typing import List

import geralt.bot as bot
import geralt.context as context
import geralt.embed as embed
import geralt.kernel.utilities.crucial as crucial
import geralt.kernel.utilities.extensions as extensions
import geralt.kernel.utilities.flags as flags
import geralt.kernel.utilities.override_jsk as overidden_jishaku
import geralt.kernel.views.errorhandler as errorhandler
import geralt.kernel.views.fun as fun
import geralt.kernel.views.help as help
import geralt.kernel.views.history as history
import geralt.kernel.views.meta as meta
import geralt.kernel.views.paginator as paginator
import geralt.kernel.views.tags as tags
import geralt.kernel.views.tickets as tickets
import geralt.kernel.views.verification as verification

COGS_EXTENSIONS: List = [
    "jishaku",
    "geralt.ext.fun",
    "geralt.ext.tags",
    "geralt.ext.meta",
    "geralt.ext.guild",
    "geralt.ext.utility",
    "geralt.ext.discord",
    "geralt.ext.developer",
    "geralt.ext.moderation",
    "geralt.kernel.listeners.events",
    "geralt.kernel.listeners.errorhandler",
]

KERNEL_EXTENSIONS: List = [
    bot,
    fun,
    help,
    meta,
    tags,
    flags,
    embed,
    history,
    tickets,
    crucial,
    context,
    paginator,
    extensions,
    verification,
    errorhandler,
    overidden_jishaku,
]
