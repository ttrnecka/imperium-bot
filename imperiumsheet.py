import gspread
from oauth2client.service_account import ServiceAccountCredentials
import random
import os

ROOT = os.path.dirname(__file__)

SPREADSHEET_ID = "1t5IoiIjPAS2CD63P6xI4hWwx9c1SEzW9AL1LJ4LK6og"
ALL_CARDS = "All Cards"
TRAINING_CARDS = "Training Cards"
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


def get_all_cards():
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(ALL_CARDS)
    return sheet.get_all_records()

def generate_player_pack(team,quality="budget"):
    pack = []
    cards = client.open_by_key(SPREADSHEET_ID).worksheet(f"{MIXED_TEAMS[team]} Cards").get_all_records()

    pack.append(pick(cards,"premium"))
    pack.append(pick(cards,quality))
    pack.append(pick(cards,quality))

    return pack

def generate_training_pack(quality="budget"):
    pack = []
    cards = client.open_by_key(SPREADSHEET_ID).worksheet(TRAINING_CARDS).get_all_records()

    pack.append(pick(cards,"premium"))
    pack.append(pick(cards,quality))
    pack.append(pick(cards,quality))

    return pack

def generate_booster_pack(quality="budget"):
    pack = []
    cards = client.open_by_key(SPREADSHEET_ID).worksheet(ALL_CARDS).get_all_records()

    pack.append(pick(cards,"premium"))
    pack.append(pick(cards,quality))
    pack.append(pick(cards,quality))

    pack.append(pick(cards,quality))
    pack.append(pick(cards,quality))

    return pack

def pick(cards,quality="budget"):

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


#if __name__ == "__main__":
    #print(Coach.load_coach("TomasTddwd").collection)
