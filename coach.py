import os
import yaml

ROOT = os.path.dirname(__file__)

class Coach:
    def __init__(self,name):
        self.name = name
        self.collection = []
        self.decks = []

    def store_coach(self):
        stream = open(self.coach_file(self.name), 'w')
        yaml.dump(self, stream)
        stream.close()

    def load_coach(name):
        if os.path.isfile(Coach.coach_file(name)) :
            stream = open(Coach.coach_file(name), 'r')
            coach = yaml.load(stream, Loader = yaml.Loader)
            stream.close()
        else:
            coach = Coach(name)
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
    def find_by_name(name):
        coaches = []
        name = name.lower()
        for root, dirs, files in os.walk(Coach.coaches_folder()):
            for filename in files:
                if name in filename.lower():
                    coaches.append(Coach.load_coach(os.path.splitext(filename)[0]))
        return coaches

    def all():
        coaches = []
        for root, dirs, files in os.walk(Coach.coaches_folder()):
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

if __name__ == "__main__":
    print(Coach.find_by_name("tomast")[0].collection)

