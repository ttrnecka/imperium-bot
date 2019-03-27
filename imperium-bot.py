# Work with Python 3.6

import logging
import discord
import imperiumsheet
import random
import os
import time
from coach import Coach, Transaction

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
            emsg="Insuficient rights"
            logger.error(emsg)
            await client.send_message(message.channel, emsg)
            return
        if message.content.startswith('!adminlist'):
            if len(args)==1:
                emsg="Username missing"
                await client.send_message(message.channel, emsg)
                return
            coaches = Coach.find_by_name(args[1])
            msg = LongMessage(client,message.channel)
            if len(coaches)==0:
                msg.add("No coaches found")
            for coach in coaches:
                msg.add(f"Coach **{coach.name}**\n")
                msg.add(f"**Bank:** {coach.account.cash} coins\n")
                msg.add("**Collection**:")
                msg.add("-" * 65 + "")
                msg.add(f"{format_pack(coach.collection_with_count())}")
                msg.add("-" * 65 + "\n")

            await msg.send()

    # list commands
    if message.content.startswith('!list'):
        coach = Coach.load_coach(str(message.author))
        order = False if "bydate" in message.content else True

        msg = LongMessage(client,message.author)
        msg.add(f"**Bank:** {coach.account.cash} coins\n")
        msg.add("**Collection**:\n")
        msg.add("-" * 65 + "")
        msg.add(f"{format_pack(coach.collection_with_count(),order)}")
        msg.add("-" * 65 + "\n")
        await msg.send()
        await client.send_message(message.channel, "Collection sent to PM")

    # genpack commands
    if message.content.startswith('!genpack'):
        if check_gen_command(cmd):
            ptype = args[1]
            if ptype=="player":
                team = args[2]
                pack = imperiumsheet.Pack(ptype,team = team)
                pack.generate()
            elif ptype=="training":
                pack = imperiumsheet.Pack(ptype)
                pack.generate()
            elif ptype=="booster":
                ptype = "booster_budget" if len(args)<3 else f"booster_{args[2]}"
                pack = imperiumsheet.Pack(ptype)
                pack.generate()

            # add error handling eventually
            coach = Coach.load_coach(str(message.author))
            t = Transaction(pack.description(),pack.price)
            coach.account.make_transaction(t)
            if t.confirmed:
                coach.add_to_collection(pack.cards)
                coach.store_coach()
                unp = Unpacker(client,message.channel)
                unp.pre_message.add(f"**{pack.description()}** for **{message.author}** - **{pack.price}** coins:\n")
                unp.pre_message.add(":gift:\n----\n")
                unp.post_message.add("----\n:tada:\n")
                unp.post_message.add(f"Remaining coins: **{coach.account.cash}**")
                unp.cards_messages.extend(format_pack(pack.cards).strip("\n").split("\n"))
                await unp.send()
                #msg = LongMessage(client,message.channel)
                #msg.add(f"**{pack.description()}** for **{message.author}** - **{pack.price}** coins:\n")
                #msg.add(f"{format_pack(pack.cards)}\n")
                #msg.add(f"Remaining coins: **{coach.account.cash}**")
                #await msg.send()
                # export
                imperiumsheet.store_all_cards()
            else:
                emsg = "Transaction could not complete"
                msg = LongMessage(client,message.channel)
                msg.add(emsg)
                logger.error(emsg)
                await msg.send()
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
        if imperiumsheet.QTY in card:
            for c in str(card[imperiumsheet.QTY]):
                msg+=number_emoji(c)
            msg+=" x "
        msg+=rarity_emoji(card["Rarity"])
        msg+=f' **{card["Card Name"]}** ({card["Rarity"]} {card["Race"]} {card["Type"]} Card)\n'
    return msg

def gen_help():
    msg="```"
    msg+="USAGE:\n"
    msg+="!genpack <type> [mixed_team] [quality]\n"
    msg+="\t<type>:\n"
    msg+="\t\tplayer\n"
    msg+="\t\ttraining\n"
    msg+="\t\tbooster\n"
    msg+="\t[mixed_team]: (player type only)\n"
    for key, name in imperiumsheet.MIXED_TEAMS.items():
        msg+=f"\t\t{key} - {name}\n"
    msg+="\t[quality]: (booster type only)\n"
    msg+="\t\tbudget (default)\n"
    msg+="\t\tpremium\n"
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

def number_emoji(number):
    switcher = {
        "0": ":zero:",
        "1": ":one:",
        "2": ":two:",
        "3": ":three:",
        "4": ":four:",
        "5": ":five:",
        "6": ":six:",
        "7": ":seven:",
        "8": ":eight:",
        "9": ":nine:",

    }
    return switcher.get(number, "")

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

    def lines(self):
        lines = []
        for part in self.parts:
            lines.extend(part.split("\n"))
        return lines

    def chunks(self):
        lines = self.lines()
        while True:
            msg=""
            if not lines:
                break
            while len(lines)>0 and len(msg + lines[0]) < self.limit:
                msg += lines.pop(0) + "\n"
            yield msg

class Unpacker:
    def __init__(self,client,channel):
        self.pre_message = LongMessage(client,channel)
        self.post_message = LongMessage(client,channel)
        self.cards_messages = []
        self.client = client
        self.channel = channel

    async def send(self):
        await self.pre_message.send()
        await self.reveal_cards()
        await self.post_message.send()
    
    async def reveal_cards(self):
        for card_message in self.cards_messages:
            secs = 3
            message = await self.client.send_message(self.channel, f"Revealing card in {secs}s")
            for i in range(secs-1,0,-1):
                time.sleep(1)
                await self.client.edit_message(message, f"Revealing card in {i}s")
            await self.client.edit_message(message, card_message)

client.run(TOKEN)
