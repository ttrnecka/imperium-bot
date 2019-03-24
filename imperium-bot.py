# Work with Python 3.6

import logging
import discord
import imperiumsheet
import random
import os

ROOT = os.path.dirname(__file__)

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename=os.path.join(ROOT, 'discord.log'), encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

with open(os.path.join(ROOT, 'TOKEN'), 'r') as token_file:
    TOKEN=token_file.read()

client = discord.Client()

GEN_QUALITY = ["premium","budget"]
GEN_PACKS = ["player","training","booster"]

@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return
    if message.content.startswith('!genpack'):
        logger.info(f"{message.author}: {message.content}")
        cmd = message.content.lower()
        if check_command(cmd):
            args = cmd.split()
            quality = args[1]
            ptype = args[2]
            if ptype=="player":
                team = args[3]
                pack = imperiumsheet.generate_player_pack(team,quality)
            elif ptype=="training":
                pack = imperiumsheet.generate_training_pack(quality)
            elif ptype=="booster":
                pack = imperiumsheet.generate_booster_pack(quality)
            msg=f"{message.author.mention}\n{format_pack(pack)}"
            await client.send_message(message.channel, msg)
        else:
            await client.send_message(message.channel, gen_help())
@client.event
async def on_ready():
    logger.info('Logged in as')
    logger.info(client.user.name)
    logger.info(client.user.id)
    logger.info('------')

def format_pack(pack):
    msg = ""
    for card in pack:
        msg+=rarity_emoji(card["Rarity"])
        msg+=f'**{card["Card Name"]}** ({card["Rarity"]} {card["Race"]} {card["Type"]} Card)\n'
        msg+="-" * 65 + "\n"
    return msg

def gen_help():
    msg="```"
    msg+="USAGE:\n"
    msg+="!genpack <quality> <type> [mixed_team]\n"
    msg+="\t<quality> - budget, premium\n"
    msg+="\t<type> - player, training, booster\n"
    msg+="\t[mixed_team]: use with player <type> only\n"
    for key, name in imperiumsheet.MIXED_TEAMS.items():
        msg+=f"\t\t{key} - {name}\n"
    msg+="```"    
    return msg

def check_command(command):
    args = command.split()
    length = len(args)
    if length not in [3,4]:
        return False
    if args[1] not in GEN_QUALITY:
        return False
    if args[2] not in GEN_PACKS:
        return False
    if length==4 and args[3] not in imperiumsheet.MIXED_TEAMS.keys():
        return False
    return True

def rarity_emoji(rarity):
    switcher = {
        "Common": "",
        "Rare": ":diamonds:",
        "Epic": ":large_blue_diamond:",
        "Legendary": ":large_orange_diamond: ",
    }
    return switcher.get(rarity, "")

client.run(TOKEN)
