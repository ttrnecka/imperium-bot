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
            coach = yaml.load(stream)
            stream.close()
        else:
            coach = Coach(name)
        return coach

    def add_to_collection(self,pack):
        self.collection.extend(pack)

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
