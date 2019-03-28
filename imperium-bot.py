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

    if message.author == client.user:
        return

    dc = DiscordCommand(message,client)
    await dc.process()

@client.event
async def on_ready():
    logger.info('Logged in as')
    logger.info(client.user.name)
    logger.info(client.user.id)
    logger.info('------')


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

class DiscordCommand:
    @classmethod
    def is_private_admin_channel(cls,dchannel):
        if "admin-channel" in dchannel.name:
            return True
        return False

    @classmethod
    def format_pack(cls,pack,is_sorted=True):
        if is_sorted:
            pack = sorted(pack, key=lambda x: (rarityorder[x["Rarity"]],x["Card Name"]))
        msg = ""
        for card in pack:
            if imperiumsheet.QTY in card:
                for c in str(card[imperiumsheet.QTY]):
                    msg+=cls.number_emoji(c)
                msg+=" x "
            msg+=cls.rarity_emoji(card["Rarity"])
            msg+=f' **{card["Card Name"]}** ({card["Rarity"]} {card["Race"]} {card["Type"]} Card)\n'
        return msg

    @classmethod
    def gen_help(cls):
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

    @classmethod
    def check_gen_command(cls,command):
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

    @classmethod
    def rarity_emoji(cls,rarity):
        switcher = {
            "Common": "",
            "Rare": ":diamonds:",
            "Epic": ":large_blue_diamond:",
            "Legendary": ":large_orange_diamond: ",
        }
        return switcher.get(rarity, "")

    @classmethod
    def number_emoji(cls,number):
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

    def __init__(self,dmessage,dclient):
        self.message = dmessage
        self.client = dclient
        self.cmd = dmessage.content.lower()
        self.args = self.cmd.split(" ")

    async def process(self):
        if self.cmd.startswith('!admin'):
            await self.__run_admin()
        if self.cmd.startswith('!list'):
            await self.__run_list()
        if self.cmd.startswith('!genpack'):
            await self.__run_genpack()

    async def __run_admin(self):
        # if not started from admin-channel
        if not self.__class__.is_private_admin_channel(self.message.channel):
            emsg="Insuficient rights"
            logger.error(emsg)
            await self.client.send_message(self.message.channel, emsg)
            return

        #adminlist cmd
        if self.message.content.startswith('!adminlist'):
            # require username argument
            if len(self.args)==1:
                emsg="Username missing"
                await self.client.send_message(self.message.channel, emsg)
                return

            coaches = Coach.find_by_name(self.args[1])
            msg = LongMessage(self.client,self.message.channel)

            if len(coaches)==0:
                msg.add("No coaches found")

            for coach in coaches:
                msg.add(f"Coach **{coach.name}**\n")
                msg.add(f"**Bank:** {coach.account.cash} coins\n")
                msg.add("**Collection**:")
                msg.add("-" * 65 + "")
                msg.add(f"{self.__class__.format_pack(coach.collection_with_count())}")
                msg.add("-" * 65 + "\n")

            await msg.send()
            return

    async def __run_list(self):
        coach = Coach.load_coach(str(self.message.author))
        order = False if "bydate" in self.message.content else True

        msg = LongMessage(self.client,self.message.author)
        msg.add(f"**Bank:** {coach.account.cash} coins\n")
        msg.add("**Collection**:\n")
        msg.add("-" * 65 + "")
        msg.add(f"{self.__class__.format_pack(coach.collection_with_count(),order)}")
        msg.add("-" * 65 + "\n")
        await msg.send()
        await self.client.send_message(self.message.channel, "Collection sent to PM")

    async def __run_genpack(self):
        if self.__class__.check_gen_command(self.cmd):
            ptype = self.args[1]
            if ptype=="player":
                team = self.args[2]
                pack = imperiumsheet.Pack(ptype,team = team)
                pack.generate()
            elif ptype=="training":
                pack = imperiumsheet.Pack(ptype)
                pack.generate()
            elif ptype=="booster":
                ptype = "booster_budget" if len(self.args)<3 else f"booster_{self.args[2]}"
                pack = imperiumsheet.Pack(ptype)
                pack.generate()

            # add error handling eventually
            coach = Coach.load_coach(str(self.message.author))
            t = Transaction(pack.description(),pack.price)
            coach.account.make_transaction(t)
            if t.confirmed:
                coach.add_to_collection(pack.cards)
                coach.store_coach()
                msg = LongMessage(self.client,self.message.channel)
                msg.add(f"**{pack.description()}** for **{self.message.author}** - **{pack.price}** coins:\n")
                msg.add(f"{self.__class__.format_pack(pack.cards)}\n")
                msg.add(f"Remaining coins: **{coach.account.cash}**")
                await msg.send()
                # export
                imperiumsheet.store_all_cards()
            else:
                emsg = "Transaction could not complete"
                msg = LongMessage(self.client,self.message.channel)
                msg.add(emsg)
                logger.error(emsg)
                await msg.send()
        else:
            await self.client.send_message(self.message.channel, gen_help())

client.run(TOKEN)
