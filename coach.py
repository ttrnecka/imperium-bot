import os
import yaml
import time
import logging

ROOT = os.path.dirname(__file__)

INIT_CASH = 15

class Coach:
    def __init__(self,name):
        self.name = name
        self.collection = []
        self.decks = []
        self.account = Account(name,INIT_CASH)

    def store_coach(self):
        stream = open(self.coach_file(self.name), 'w')
        yaml.dump(self, stream)
        stream.close()

    @staticmethod
    def load_coach(name):
        if os.path.isfile(Coach.coach_file(name)) :
            stream = open(Coach.coach_file(name), 'r')
            coach = yaml.load(stream, Loader = yaml.Loader)
            stream.close()
        else:
            coach = Coach(name)
        # handlign the case when old coach account is loaded - can be removed after cleaup
        if not hasattr(coach,"account"):
            coach.account = Account(name,INIT_CASH)
        return coach

    def add_to_collection(self,pack):
        self.collection.extend(pack)

    def collection_with_count(self):
        new_collection = {}
        for card in self.collection:
            if card["Card Name"] in new_collection:
                new_collection[card["Card Name"]]["Quantity"] += 1
            else:
                new_collection[card["Card Name"]] = card
                new_collection[card["Card Name"]]["Quantity"] = 1
        return list(new_collection.values())

    # returns array of Coaches that meet the name
    @staticmethod
    def find_by_name(name):
        coaches = []
        name = name.lower()
        for _, _, files in os.walk(Coach.coaches_folder()):
            for filename in files:
                if name in filename.lower():
                    coaches.append(Coach.load_coach(os.path.splitext(filename)[0]))
        return coaches

    @staticmethod
    def all():
        coaches = []
        for _, _, files in os.walk(Coach.coaches_folder()):
            for filename in files:
                coaches.append(Coach.load_coach(os.path.splitext(filename)[0]))
        return coaches

    @staticmethod
    def coach_file(name):
        fn = os.path.join(Coach.coaches_folder(), f"{name}.yaml")
        return fn

    @staticmethod
    def coaches_folder():
        try:
            folder = os.path.join(ROOT,"data","coaches")
            os.makedirs(folder)
        except FileExistsError:
            pass
        return folder

class Account:

    logger = logging.getLogger('transaction')
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(filename=os.path.join(ROOT, 'transaction.log'), encoding='utf-8', mode='a')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)

    def __init__(self,coach_name,cash=15):
        self.cash = cash
        self.coach_name = coach_name
        self.transactions = []

    def make_transaction(self,transaction):
        # do nothing
        if self.cash < transaction.price:
            raise TransactionError("Insuficient Funds")
        if transaction.confirmed:
            raise TransactionError("Double processing of transaction")

        try:
            self.cash -= transaction.price
            transaction.confirm()
            self.transactions.append(transaction)
            Account.logger.info(f"{self.coach_name}: {transaction.comodity} for {transaction.price}")
        except Exception as e:
            raise TransactionError(str(e))

        return transaction



class Transaction:
    """
    Simple 1 comodity transaction used for pack generators
    """
    def __init__(self,comodity,price):
        self.price = price
        self.comodity = comodity
        self.created_at = time.time()
        self.confirmed = False

    def confirm(self):
        self.confirmed = True
        self.confirmed_at = time.time()

class TransactionError(Exception):
    pass

#if __name__ == "__main__":

