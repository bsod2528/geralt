"""
[Geralt]
Copyright (C) 2021 - 2023 BSOD2528

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU AGPL-3.0 License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/agpl-3.0.en.html>.
"""

from .bot import BaseBot
from .context import BaseContext
from .embed import BaseEmbed
from .kernel.utilities.crucial import (misc, Plural,
                                       total_lines,
                                       TabulateData,
                                       WebhookManager)
