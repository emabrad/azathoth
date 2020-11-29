#!/usr/bin/env python3
import os
import re
import discord
import logging
import asyncio

from random import randint

logging.basicConfig(level=logging.INFO)

client = discord.Client()
discord.opus.load_opus
roll_command = "!pls"

first_connect = True
last_playing_index = -1
playing_quotes = {1: "with dice", 2: "second item"}

COL_CRIT_SUCCESS = 0xFFFFFF
COL_EXTR_SUCCESS = 0xF1C40F
COL_HARD_SUCCESS = 0x2ECC71
COL_NORM_SUCCESS = 0x2E71CC
COL_NORM_FAILURE = 0xE74C3C
COL_CRIT_FAILURE = 0x992D22


class DiceResult:
    def __init__(self, title=None, desc=None, colour=COL_NORM_SUCCESS):
        self.title = title
        self.desc = desc
        self.colour = COL_NORM_SUCCESS


def roll_die(min=1, max=10):
    result = randint(min, max)
    return result


def resolve_dice(bonus_die, penalty_die, threshold):
    ten_result = roll_die(0, 9)
    ten_result_pool = [ten_result]
    one_result = roll_die()

    if bonus_die > 0 and penalty_die > 0:
        return "Can't chain bonus and penalty dice"

    for i in range(bonus_die):
        ten_result_pool.append(roll_die(0, 9))

    for i in range(penalty_die):
        ten_result_pool.append(roll_die(0, 9))

    ten_result = max(ten_result_pool) if penalty_die else min(ten_result_pool)
    combined_result = (ten_result * 10) + one_result
    desc = "%d(%s) + %d = %d" % (
        ten_result * 10,
        "/".join([str(i * 10) for i in ten_result_pool]),
        one_result,
        combined_result,
    )
    if not threshold:
        return desc

    if combined_result == 1:
        title, colour = "Critical Success!", COL_CRIT_SUCCESS
    elif combined_result == 100:
        title, colour = "Critical Failure!", COL_CRIT_FAILURE
    elif combined_result <= threshold / 5:
        title, colour = "Extreme Success!", COL_EXTR_SUCCESS
    elif combined_result <= threshold / 2:
        title, colour = "Hard Success!", COL_HARD_SUCCESS
    elif combined_result <= threshold:
        title, colour = "Success", COL_NORM_SUCCESS
    else:
        title, colour = "Failure", COL_NORM_FAILURE

    return DiceResult(title, colour, desc)


def parse_roll(dice_string):
    fail = """
Unable to parse dice command. Usage:
```
/croll [[number=1][die type]]...[[score][threshold]]

Die Types:
    b: Bonus dice (can't be chained with Penalty)
    p: Penalty dice (can't be chained with Bonus)
    t: threshold to determine success/fail. Score is required if a threshold is set.

Examples:
    /croll
    36

    /croll 60t
    Hard Success: 24

    /croll b
    70/30 + 5 = 35

    /croll 2p70t
    A
    Failure: 0/50/70 + 4 = 74
```
"""
    dice = [x for x in re.split(r"(\d*?[bpt])", dice_string) if x]

    if len(dice) > 1 and "b" in dice_string and "p" in dice_string:
        return "Can't chain bonus and penalty dice"

    bonus_die = 0
    penalty_die = 0
    threshold = False

    for die in dice:
        default_num = False
        s = re.search(r"(\d*?)([bpt])", die)
        if not s:
            default_num = True
            die = "1" + die
        s = re.search(r"(\d*?)([bpt])", die)
        if not s:
            return fail
        g = s.groups()
        if len(g) != 2:
            return fail
        try:
            num = int(g[0])
        except:
            default_num = True
            num = 1

        die_code = g[1]

        if len(die_code) > 1:
            return fail

        if die_code == "b":
            bonus_die = num

        if die_code == "p":
            penalty_die = num

        if die_code == "t":
            if default_num:
                return "threshold requires a value!"
            else:
                threshold = num

    return resolve_dice(bonus_die, penalty_die, threshold)


@client.event
async def on_ready():
    global first_connect
    print("Azathoth connected")
    if first_connect:
        first_connect = False


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith(roll_command):
        result = parse_roll(message.content[len(roll_command) + 1 :])
        if isinstance(result, str):
            await message.channel.send(result)
        else:
            em = discord.Embed(title=result.title, description=result.desc, colour=result.colour)
            em.set_footer(text=result.desc)
            em.description = None
            await message.channel.send(embed=em)


token = os.environ["AZATHOTH_TOKEN"]
client.run(token)
