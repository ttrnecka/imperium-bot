import gspread
from oauth2client.service_account import ServiceAccountCredentials
import random
import os
from coach import Coach

ROOT = os.path.dirname(__file__)

# use creds to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name(os.path.join(ROOT, 'client_secret.json'), scope)

class ImperiumSheet:
    SPREADSHEET_ID = "1t5IoiIjPAS2CD63P6xI4hWwx9c1SEzW9AL1LJ4LK6og"
    ALL_CARDS_SHEET = "All Cards"
    TRAINING_CARDS_SHEET = "Training Cards"
    STARTER_PACK_SHEET="Starter Pack"

    MASTERSHEET_ID = "1wL-qA6yYxaYkpvzL7KfwxNzJOsj0E17AEwSndSp7vNY"
    MASTER_NAME = "Master List"

    QTY = "Quantity"

    CARD_HEADER = [
        "Coach",
        "Rarity",
        "Type",
        "Subtype",
        "Card Name",
        "Race",
        "Description",
        "Notes"
    ]
    MASTER_LIST_HEADER = ["Coach"] + CARD_HEADER

    MIXED_TEAMS = [
        {"code":"aog",  "name":"Alliance of Goodness",   "races":['Bretonnian' , 'Human', 'Dwarf', 'Halfling', 'Wood Elf'] },
        {"code":"au",   "name":'Afterlife United',       "races":['Undead','Necromantic','Khemri','Vampire']},
        {"code":"afs",  "name":'Anti-Fur Society',       "races":['Kislev' , 'Norse', 'Amazon', 'Lizardman']},
        {"code":"cgs",  "name":'Chaos Gods Selection',   "races":['Chaos' , 'Nurgle']},
        {"code":"cpp",  "name":'Chaotic Player Pact',    "races":['Chaos' , 'Skaven', 'Dark Elf', 'Underworld Denizens']},
        {"code":"egc",  "name":'Elfic Grand Coalition',  "races":['High Elf' , 'Dark Elf', 'Wood Elf', 'Pro Elf']},
        {"code":"fea",  "name":'Far East Association',   "races":['Chaos Dwarf' , 'Orc', 'Goblin', 'Skaven', 'Ogre']},
        {"code":"hl",   "name":'Human League',           "races":['Bretonnian' , 'Human', 'Kislev', 'Norse', 'Amazon']},
        {"code":"sbr",  "name":'Superior Being Ring',    "races":['Bretonnian' , 'High Elf', 'Vampire', 'Chaos Dwarf']},
        {"code":"uosp", "name":'Union of Small People',  "races":['Ogre' , 'Goblin','Halfling']},
        {"code":"vt",   "name":'Violence Together',      "races":['Ogre' , 'Goblin','Halfling']}
    ]

    @classmethod
    def cards(cls):
        if hasattr(cls,"_cards"):
            return cls._cards
        # if they are not leaded yet do it
        client = gspread.authorize(creds)
        sheet = client.open_by_key(cls.SPREADSHEET_ID).worksheet(cls.ALL_CARDS_SHEET)
        cls._cards = sheet.get_all_records()
        return cls._cards

    @classmethod
    def filter_cards(cls,rarity,ctype=None,races=None):
        if races is not None:
            return [card for card in cls.cards() if card["Rarity"]==rarity and card["Type"]==ctype and card["Race"] in races]
        if ctype is not None:
            return [card for card in cls.cards() if card["Rarity"]==rarity and card["Type"]==ctype]
        return [card for card in cls.cards() if card["Rarity"]==rarity]

    @classmethod
    def rarity(cls,pack_type, quality):
        budgetCommon = 80+1;
        budgetRare = 95+1;
        budgetEpic = 99+1;
        budgetLegendary = 100+1;
        trainingCommon = 65+1;
        trainingRare = 97+1;
        trainingEpic = 100+1;
        premiumRare = 65+1;
        premiumEpic = 97+1;
        premiumLegendary = 100+1;

        roll = random.randint(1,100)

        if pack_type=='booster' and quality == "budget":
            if roll in range(budgetEpic,budgetLegendary):
                rarity = "Legendary"
            elif roll in range(budgetRare,budgetEpic):
                rarity = "Epic"
            elif roll in range(budgetCommon,budgetRare):
                rarity = "Rare"
            else:
                rarity = "Common"
        elif pack_type=="training":
            if roll in range(trainingRare,trainingEpic):
                rarity = "Epic"
            elif roll in range(trainingCommon,trainingRare):
                rarity = "Rare"
            else:
                rarity = "Common"
        else:
            if roll in range(premiumEpic,premiumLegendary):
                rarity = "Legendary"
            elif roll in range(premiumRare,premiumEpic):
                rarity = "Epic"
            else:
                rarity = "Rare"

        return rarity

    @classmethod
    def genpack(cls,pack_type,quality="budget",team=None):
        if team is not None and team not in cls.team_codes():
            raise cls.InvalidTeam(team)

        if quality not in ["premium","budget"]:
            raise cls.InvalidQuality(quality)

        if pack_type not in ["player","booster","training","starter"]:
            raise cls.InvalidPackType(pack_type)

        cards = []

        if pack_type == "booster":
            rarity = cls.rarity(pack_type,"premium")
            fcards = cls.filter_cards(rarity)
            cards.append(random.choice(fcards))
            for _ in range(4):
                rarity = cls.rarity(pack_type,quality)
                fcards = cls.filter_cards(rarity)
                cards.append(random.choice(fcards))

        if pack_type == "training":
            for _ in range(3):
                rarity = cls.rarity(pack_type,"premium")
                fcards = cls.filter_cards(rarity,"Training")
                cards.append(random.choice(fcards))

        if pack_type == "player":
            races = cls.team_by_code(team)["races"]
            for _ in range(3):
                rarity = cls.rarity(pack_type,"premium")
                fcards = cls.filter_cards(rarity,"Player",races)
                cards.append(random.choice(fcards))

        if pack_type == "starter":
            client = gspread.authorize(creds)
            sheet = client.open_by_key(cls.SPREADSHEET_ID).worksheet(cls.STARTER_PACK_SHEET)
            summed_cards = sheet.get_all_records()
            for card in summed_cards:
                count = card[cls.QTY]
                del card[cls.QTY]
                for _ in range(count):
                    cards.append(card)

        return cards

    @classmethod
    def team_by_code(cls,code):
        return next(t for t in cls.MIXED_TEAMS if t["code"] == code)

    @classmethod
    def team_codes(cls):
        return [team["code"] for team in cls.MIXED_TEAMS]

    @classmethod
    def store_all_cards(cls):
        client = gspread.authorize(creds)
        ws = client.open_by_key(cls.MASTERSHEET_ID)
        try:
            sheet = ws.worksheet(cls.MASTER_NAME)
        except gspread.exceptions.WorksheetNotFound:
            sheet = ws.add_worksheet(title=cls.MASTER_NAME,rows=100, cols=15)

        sheet.clear()

        cards = []
        cards.append(cls.MASTER_LIST_HEADER)

        for coach in Coach.all():
            for card in coach.collection:
                card["Coach"]=coach.name
                cards.append(card)

        cards_amount, keys_amount = len(cards), len(cls.MASTER_LIST_HEADER)

        cell_list = sheet.range(f"A1:{gspread.utils.rowcol_to_a1(cards_amount, keys_amount)}")

        for cell in cell_list:
            if cell.row==1:
                cell.value = cards[cell.row-1][cell.col-1]
            else:
                cell.value = cards[cell.row-1][cls.MASTER_LIST_HEADER[cell.col-1]]
        sheet.update_cells(cell_list)

    class InvalidTeam(Exception):
        pass

    class InvalidQuality(Exception):
        pass

    class InvalidPackType(Exception):
        pass

PACK_PRICES = {
    "booster_budget": 5,
    "booster_premium": 20,
    "player": 25,
    "training": 10,
    "starter": 0
}
class Pack:
    def __init__(self,ptype="booster_budget",team = None):
        if ptype not in PACK_PRICES:
            raise ValueError(f"Pack type {ptype} unknow")
        self.pack_type = ptype
        if self.pack_type == "player":
            if not team:
                raise  ValueError(f"Missing team value for {ptype} pack")
            elif team.lower() not in ImperiumSheet.team_codes():
                raise  ValueError(f"Team {team} unknow")
            else:
                self.team = team.lower()
        self.price = PACK_PRICES[ptype]

    def generate(self):
        if self.pack_type == "starter":
            self.cards = ImperiumSheet.genpack("starter")
        if self.pack_type == "player":
            self.cards = ImperiumSheet.genpack("player","premium",self.team)
        if self.pack_type == "training":
            self.cards = ImperiumSheet.genpack("training")
        if self.pack_type in ["booster_budget","booster_premium"] :
            q = "budget" if "budget" in self.pack_type else "premium"
            self.cards = ImperiumSheet.genpack("booster",q)

    def description(self):
        desc = ' '.join(self.pack_type.split('_')).capitalize()
        if hasattr(self,'team'):
            desc+=" " + ImperiumSheet.team_by_code(self.team)["name"]
        desc+=" pack"

        return desc

if __name__ == "__main__":
    #p = Pack("starter")
    #p.generate()
    print(ImperiumSheet.genpack("starter"))
