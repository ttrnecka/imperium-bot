import gspread
from oauth2client.service_account import ServiceAccountCredentials
import random
import os
from coach import Coach

ROOT = os.path.dirname(__file__)

SPREADSHEET_ID = "1t5IoiIjPAS2CD63P6xI4hWwx9c1SEzW9AL1LJ4LK6og"
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
]
MASTER_LIST_HEADER = ["Coach"] + CARD_HEADER

ALL_CARDS_SHEET = "All Cards"
TRAINING_CARDS_SHEET = "Training Cards"
STARTER_PACK_SHEET="Starter Pack"
MIXED_TEAMS = {
    "aog": "Alliance of Goodness",
    "au": "Afterlife United",
    "afs": "Anti-Fur Society",
    "cgs": "Chaos Gods Selection",
    "cpp":"Chaotic Player Pact",
    "hl": "Human League",
    "egc": "Elfic Grand Coalition",
    "fea": "Far East Association",
    "sbr": "Superior Being Ring",
    "uosp": "Union of Small People",
    "vt": "Violence Together"
}

# use creds to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name(os.path.join(ROOT, 'client_secret.json'), scope)
client = gspread.authorize(creds)


def store_all_cards():
    ws = client.open_by_key(MASTERSHEET_ID)
    try:
        sheet = ws.worksheet(MASTER_NAME)
    except gspread.exceptions.WorksheetNotFound:
        sheet = ws.add_worksheet(title=MASTER_NAME,rows=100, cols=15)

    sheet.clear()

    cards = []
    cards.append(MASTER_LIST_HEADER)

    for coach in Coach.all():
        for card in coach.collection:
            card["Coach"]=coach.name
            cards.append(card)

    cards_amount, keys_amount = len(cards), len(MASTER_LIST_HEADER)

    cell_list = sheet.range(f"A1:{gspread.utils.rowcol_to_a1(cards_amount, keys_amount)}")

    for cell in cell_list:
        if cell.row==1:
            cell.value = cards[cell.row-1][cell.col-1]
        else:
            cell.value = cards[cell.row-1][MASTER_LIST_HEADER[cell.col-1]]
    sheet.update_cells(cell_list)

def all_cards():
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(ALL_CARDS_SHEET)
    return sheet.get_all_records()


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
            elif team.lower() not in MIXED_TEAMS:
                raise  ValueError(f"Team {team} unknow")
            else:
                self.team = team.lower()
        self.price = PACK_PRICES[ptype]

    def generate(self):
        if self.pack_type == "starter":
            self.cards = self.__starter_pack()
        if self.pack_type == "player":
            self.cards = self.__player_pack()
        if self.pack_type == "training":
            self.cards = self.__training_pack()
        if self.pack_type in ["booster_budget","booster_premium"] :
            q = "budget" if "budget" in self.pack_type else "premium"
            self.cards = self.__booster_pack(q)

    def description(self):
        desc = ' '.join(self.pack_type.split('_')).capitalize()
        if hasattr(self,'team'):
            desc+=" " + MIXED_TEAMS[self.team]
        desc+=" pack"

        return desc
    
    def __starter_pack(self):
        sheet = client.open_by_key(SPREADSHEET_ID).worksheet(STARTER_PACK_SHEET)
        summed_cards = sheet.get_all_records()
        cards = []
        for card in summed_cards:
            count = card[QTY]
            del card[QTY]
            for _ in range(count):
                cards.append(card)
        return cards

    def __player_pack(self):
        cards = []
        quality = "premium"
        all_cards = client.open_by_key(SPREADSHEET_ID).worksheet(f"{MIXED_TEAMS[self.team]} Cards").get_all_records()
        for _ in range(3):
            cards.append(self.__pick(all_cards,quality))
        return cards

    def __training_pack(self):
        cards = []
        quality = "premium"
        all_cards = client.open_by_key(SPREADSHEET_ID).worksheet(TRAINING_CARDS_SHEET).get_all_records()
        for _ in range(3):
            cards.append(self.__pick(all_cards,quality))
        return cards

    def __booster_pack(self,quality="budget"):
        cards = []
        all_cards = client.open_by_key(SPREADSHEET_ID).worksheet(ALL_CARDS_SHEET).get_all_records()

        cards.append(self.__pick(all_cards,"premium"))
        for _ in range(4):
            cards.append(self.__pick(all_cards,quality))
        return cards

    def __pick(self,cards,quality="budget"):

        quality = quality.capitalize()
        max_weight = int(cards[-1][f"Weighted Value ({quality})"])
        pick_weight = random.randint(0,max_weight)

        for i,card in enumerate(cards):
            # ignore cards with empty weighted value
            if card[f"Weighted Value ({quality})"]=="":
                continue

            # if the pick and current values are equal it is the card
            current_weight = int(card[f"Weighted Value ({quality})"])
            if current_weight == pick_weight:
                return card
            # else if the current os already higher we select the current or the previous, whichever is closer
            elif current_weight > pick_weight:
                # pick the one that is closer
                if (current_weight - pick_weight) > (pick_weight - int(cards[i-1][f"Weighted Value ({quality})"])):
                    return cards[i-1]
                else:
                    return card


if __name__ == "__main__":
    p = Pack("booster_premium", team="Hl")
    p.generate()
    print(p.cards)
