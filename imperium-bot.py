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

TOKEN = 'NTU4OTcxMTkwOTYyNjgzOTA0.D3emLQ.A6G8xqEd-W8s_gNojPZy2iRjR54'
client = discord.Client()
cards=imperiumsheet.get_all_cards()
#logger.info(cards)

@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return
    print(message.content)
    if message.content.startswith('!hello'):
        msg = 'Hello {0.author.mention}'.format(message)
        await client.send_message(message.channel, msg)

    if message.content.startswith('!random_card'):
        card = random.choice(cards)
        msg = 'Race: {2}, Type: {3}, Rarity: {4}, Name: {1}  {0.author.mention}'.format(message,card["Card Name"],card["Race"],card["Type"],card["Rarity"])
        await client.send_message(message.channel, msg)

    if message.content.startswith('!genpack'):
        cmd = message.content.lower()
        if check_command(cmd):
            text = cmd.split()
            ptype = text[2]
            quality = text[1]
            if ptype=="player":
                team = text[3]
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
    len_name =len_race = len_type = len_rare = 0
    msg = ""
    for card in pack:
        if len(card["Card Name"])>len_name:
            len_name = len(card["Card Name"])
        if len(card["Race"])>len_race:
            len_race = len(card["Race"])
        if len(card["Type"])>len_type:
            len_type = len(card["Type"])
        if len(card["Rarity"])>len_rare:
            len_rare = len(card["Rarity"])
    for card in pack:
        msg+=f'**{card["Card Name"]}**: {card["Rarity"]} {card["Race"]} {card["Type"]}\n'
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
    if args[1] not in ["premium","budget"]:
        return False
    if args[2] not in ["player","training","booster"]:
        return False
    if length==4 and args[3] not in imperiumsheet.MIXED_TEAMS.keys():
        return False
    return True

client.run(TOKEN)
