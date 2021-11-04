import discord
import json
from discord.ext import commands
import datetime
from dateutil.relativedelta import relativedelta



def write_json(file, contents):
    with open(file, 'w') as newfile:
        json.dump(contents, newfile, ensure_ascii = True, indent = 4)

def get_uptime(bot: commands.Bot) -> str:
    delta_uptime = relativedelta(datetime.datetime.now(), bot.launch_time)
    days, hours, minutes, seconds = delta_uptime.days, delta_uptime.hours, delta_uptime.minutes, delta_uptime.seconds

    uptimes = {x[0]: x[1] for x in [('day', days), ('hour', hours), ('minute', minutes), ('second', seconds)] if x[1]}
    l = len(uptimes) 

    last = " ".join(value for index, value in enumerate(uptimes.keys()) if index == len(uptimes)-1)

    uptime_string = ", ".join(
        f"{uptimes[value]} {value}{'s' if uptimes[value] > 1 else ''}" for index, value in enumerate(uptimes.keys()) if index != l-1
    )
    uptime_string += f" and {uptimes[last]}" if l > 1 else f"{uptimes[last]}"
    uptime_string += f" {last}{'s' if uptimes[last] > 1 else ''}"
        
    return uptime_string