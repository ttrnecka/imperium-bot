# Work with Python 3.6

import logging
import discord
import imperiumsheet
import random
import os
from coach import Coach

ROOT = os.path.dirname(__file__)

#logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename=os.path.join(ROOT, 'discord.log'), encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

with open(os.path.join(ROOT, 'TOKEN'), 'r') as token_file:
    TOKEN=token_file.read()

client = discord.Client()

GEN_QUALITY = ["premium","budget"]
GEN_PACKS = ["player","training","booster"]
rarityorder={"Common":100, "Rare":10, "Epic":5, "Legendary":1}


@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    logger.info(f"{message.author}: {message.content}")
    cmd = message.content.lower()
    args = cmd.split()

    if message.author == client.user:
        return
    # admin commands
    if message.content.startswith('!admin'):
        if not is_private_admin_channel(message.channel):
            await client.send_message(message.channel, "Insuficient rights")
            return
        if message.content.startswith('!adminlist'):
            if len(args)==1:
                await client.send_message(message.channel, "Username missing")
                return
            coaches = Coach.find_by_name(args[1])
            msg = LongMessage(client,message.channel)
            #msg.add(f"{message.author.mention}\n")
            if len(coaches)==0:
                msg.add("No coaches found")
            for coach in coaches:
                msg.add(f"**{coach.name} collection:**\n")
                msg.add("-" * 65 + "\n")
                msg.add(f"{format_pack(coach.collection)}")
                msg.add("-" * 65 + "\n\n")
            
            await msg.send()

    # list commands
    if message.content.startswith('!list'):
        coach = Coach.load_coach(str(message.author))
        order = False if "bydate" in message.content else True

        msg = LongMessage(client,message.author)
        msg.add("**Collection**:\n\n")
        msg.add(f"{format_pack(coach.collection,order)}")
        await msg.send()
        await client.send_message(message.channel, "Collection sent to PM")

    # genpack commands
    if message.content.startswith('!genpack'):
        if check_gen_command(cmd):
            ptype = args[1]
            if ptype=="player":
                team = args[2]
                pack = imperiumsheet.generate_player_pack(team,"premium")
            elif ptype=="training":
                pack = imperiumsheet.generate_training_pack("premium")
            elif ptype=="booster":
                quality = "budget" if len(args)<3 else args[2]
                pack = imperiumsheet.generate_booster_pack(quality)

            # add error handling eventually
            coach = Coach.load_coach(str(message.author))
            coach.add_to_collection(pack)
            coach.store_coach()

            msg = LongMessage(client,message.channel)
            msg.add(f"Pack for **{message.author}**:\n{format_pack(pack)}")
            await msg.send()

            # export
            imperiumsheet.store_all_cards()
        else:
            await client.send_message(message.channel, gen_help())
@client.event
async def on_ready():
    logger.info('Logged in as')
    logger.info(client.user.name)
    logger.info(client.user.id)
    logger.info('------')

def format_pack(pack,is_sorted=True):
    if is_sorted:
        pack = sorted(pack, key=lambda x: (rarityorder[x["Rarity"]],x["Card Name"]))
    msg = ""
    for card in pack:
        msg+=rarity_emoji(card["Rarity"])
        msg+=f'**{card["Card Name"]}** ({card["Rarity"]} {card["Race"]} {card["Type"]} Card)\n'
    return msg

def gen_help():
    msg="```"
    msg+="USAGE:\n"
    msg+="!genpack <type> [mixed_team] [quality]\n"
    msg+="\t<type> - player, training, booster\n"
    msg+="\t[mixed_team]: (player only)\n"
    for key, name in imperiumsheet.MIXED_TEAMS.items():
        msg+=f"\t\t{key} - {name}\n"
    msg+="\t[quality] - budget, premium (booster only)\n"
    msg+="```"
    return msg

def is_private_admin_channel(dchannel):
    if "admin-channel" in dchannel.name:
        return True
    return False

def check_gen_command(command):
    args = command.split()
    length = len(args)
    if length not in [2,3]:
        return False
        
    if args[1] not in GEN_PACKS:
        return False
    # training/booster without quality
    if length == 2 and args[1] not in ["training","booster"]:
        return False
    # booster with allowed quality
    if length == 3 and args[1]=="booster" and args[2] not in GEN_QUALITY:
        return False
    # player with teams 
    if length == 3 and args[1]=="player" and args[2] not in imperiumsheet.MIXED_TEAMS.keys():
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

class LongMessage:
    def __init__(self,client,channel):
        self.limit = 2000
        self.parts = []
        self.client = client
        self.channel=channel

    def add(self,part):
        self.parts.append(part)

    async def send(self):
        for chunk in self.chunks():
            await self.client.send_message(self.channel, chunk)

    def chunks(self):
        while True:
            msg=""
            if not self.parts:
                break
            while len(self.parts)>0 and len(msg + self.parts[0]) < self.limit:
                msg += self.parts.pop(0)
            yield msg
client.run(TOKEN)
