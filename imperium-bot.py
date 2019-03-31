# Work with Python 3.6

import logging
import discord
from imperiumbase import ImperiumSheet, Pack, PACK_PRICES
import random
import os
import time
from coach import Coach, Transaction, TransactionError

ROOT = os.path.dirname(__file__)
RULES_LINK = "https://goo.gl/GqWRwD"

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
            pack = Pack.sort_by_rarity(pack)
        msg = ""
        for card in pack:
            if ImperiumSheet.QTY in card:
                for c in str(card[ImperiumSheet.QTY]):
                    msg+=cls.number_emoji(c)
                msg+=" x "
            msg+=cls.rarity_emoji(card["Rarity"])
            msg+=f' **{card["Card Name"]}** ({card["Rarity"]} {card["Race"]} {card["Type"]} Card)\n'
        return msg.strip("\n")

    @classmethod
    def gen_help(cls):
        msg="```asciidoc\n"
        msg+="!genpack command generates new pack and assigns it to coach. The coach needs to have enough coins to buy the pack.\n \n"
        msg+="= Booster budget pack =\n"
        msg+="Content: 5 cards of any type\n"
        msg+=f"Price: {PACK_PRICES['booster_budget']} coins\n"
        msg+="Rarity: 1 Rare and higher rarity, 4 Common and higher rarity\n"
        msg+="Command: !genpack booster\n \n"

        msg+="= Booster budget pack PREMIUM =\n"
        msg+="Content: 5 cards any type\n"
        msg+=f"Price: {PACK_PRICES['booster_premium']} coins\n"
        msg+="Rarity: Rare and higher\n"
        msg+="Command: !genpack booster premium\n \n"

        msg+="= Training pack =\n"
        msg+="Content: 3 training type cards\n"
        msg+=f"Price: {PACK_PRICES['training']} coins\n"
        msg+="Rarity: Commom or higher\n"
        msg+="Command: !genpack training\n \n"

        msg+="= Player pack =\n"
        msg+="Content: 3 player type cards\n"
        msg+=f"Price: {PACK_PRICES['player']} coins\n"
        msg+="Rarity: Rare or higher\n"
        msg+="Command: !genpack player <team>\n"
        msg+="where <team> is one of following:\n"
        for team in ImperiumSheet.MIXED_TEAMS:
            msg+="\t"+team["code"] +" - "+ team["name"] +"\n"

        msg+="```"
        return msg

    @classmethod
    def adminbank_help(cls):
        msg="```"
        msg+="USAGE:\n"
        msg+="!adminbank <amount> <coach> <reason>\n"
        msg+="\t<amount>: number of coins to add to bank, if negative is used, it will be deducted from bank\n"
        msg+="\t<coach>: coach discord name, must be unique\n"
        msg+="\t<reason>: describe why you are changing the coach bank\n"
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
        # training takes not other parameter
        if length > 2 and args[1]=="training":
            return False
        # booster with allowed quality
        if length == 3 and args[1]=="booster" and args[2] not in GEN_QUALITY:
            return False
        # player with teams
        if length == 3 and args[1]=="player" and args[2] not in ImperiumSheet.team_codes():
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

    async def transaction_error(self,error):
        text = type(error).__name__ +": "+str(error)
        msg = LongMessage(self.client,self.message.channel)
        msg.add(text)
        await msg.send()
        logger.error(text)

    def __init__(self,dmessage,dclient):
        self.message = dmessage
        self.client = dclient
        self.cmd = dmessage.content.lower()
        self.args = self.cmd.split(" ")

    async def process(self):
        try:
            if self.cmd.startswith('!admin'):
                await self.__run_admin()
            if self.cmd.startswith('!list'):
                await self.__run_list()
            if self.cmd.startswith('!genpack'):
                await self.__run_genpack()
            if self.cmd.startswith('!newcoach'):
                await self.__run_newcoach()
        except ValueError as e:
            await self.transaction_error(e)
        except Exception as e:
            await self.transaction_error(e)
            #raising will not kill the discrod bot but will cause it to log this to error.log as well
            raise

    async def __run_newcoach(self):
        name = str(self.message.author)
        if Coach.exists(name):
            msg = LongMessage(self.client,self.message.channel)
            msg.add(f"**{self.message.author.mention}** account exists already\n")
            await msg.send()
        else:
            coach = Coach.load_coach(str(self.message.author))
            coach.store_coach()
            # transaction is ok and coach is saved
            msg = LongMessage(self.client,self.message.channel)
            msg.add(f"**{self.message.author.mention}** account created\n")
            msg.add(f"**Bank:** {coach.account.cash} coins")
            msg.add(f"**Rules**: <{RULES_LINK}>")
            await msg.send()

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
        if self.message.content.startswith('!adminbank'):
            # require username argument
            if len(self.args)<4:
                emsg="Not enough arguments!!!\n"
                await self.client.send_message(self.message.channel, emsg)
                await self.client.send_message(self.message.channel, self.__class__.adminbank_help())
                return

            # amount must be int
            if not RepresentsInt(self.args[1]):
                emsg="<amount> is not whole number!!!\n"
                await self.client.send_message(self.message.channel, emsg)
                return

            # find coach
            coaches = Coach.find_by_name(self.args[2])
            if len(coaches)==0:
                emsg=f"Coach __{self.args[2]}__ not found!!!\n"
                await self.client.send_message(self.message.channel, emsg)
                return

            if len(coaches)>1:
                emsg=f"Coach __{self.args[2]}__ not **unique**!!!\n"
                emsg+="Select one: "
                for coach in coaches:
                    emsg+=coach.name
                    emsg+=" "
                await self.client.send_message(self.message.channel, emsg)
                return

            amount = int(self.args[1])
            coach = coaches[0]
            reason = ' '.join(str(x) for x in self.message.content.split(" ")[3:]) + " - updated by " + str(self.message.author)

            t = Transaction(reason,-1*amount)
            try:
                coach.make_transaction(t)
            except TransactionError as e:
                await self.transaction_error(e)
                return
            else:
                msg = LongMessage(self.client,self.message.channel)
                msg.add(f"Bank for {coach.name} updated to **{coach.account.cash}** coins:\n")
                msg.add(f"Note: {reason}\n")
                msg.add(f"Change: {amount} coins")
                await msg.send()

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
                pack = Pack(ptype,team = team)
                pack.generate()
            elif ptype=="training":
                pack = Pack(ptype)
                pack.generate()
            elif ptype=="booster":
                ptype = "booster_budget" if len(self.args)<3 else f"booster_{self.args[2]}"
                pack = Pack(ptype)
                pack.generate()

            # add error handling eventually
            coach = Coach.load_coach(str(self.message.author))
            t = Transaction(pack,pack.price)
            try:
                coach.make_transaction(t)
            except TransactionError as e:
                await self.transaction_error(e)
                return
            else:
                # transaction is ok and coach is saved
                msg = LongMessage(self.client,self.message.channel)
                msg.add(f"**{pack.description()}** for **{self.message.author}** - **{pack.price}** coins:\n")
                msg.add(f"{self.__class__.format_pack(pack.cards)}\n")
                msg.add(f"**Bank:** {coach.account.cash} coins")
                await msg.send()
                # export
                ImperiumSheet.store_all_cards()
        else:
            await self.client.send_message(self.message.channel, self.__class__.gen_help())

def RepresentsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

client.run(TOKEN)
