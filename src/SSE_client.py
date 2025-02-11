from Cryptodome.Random import get_random_bytes
from os.path import exists
from os import makedirs

class Client:
    def __init__(self, name):
        self.name, self.key = name, get_random_bytes(16)
        self.path = "./src/Client/" + name + "/"
        if not exists(self.path):
            makedirs(self.path)
            raise Exception("L'environnement du client " + name + " n'existait pas, il a été crée.")

    def get_key(self):
        return self.key

    def get_path(self):
        return self.path

    def __str__(self):
        return self.name + " : " + str(self.key)

    def send_index(self):
        with open(self.path + "index.json", "r", encoding="utf-8") as index_client:
            new_index = json.load(index_client)
        with open(self.path + "index.json", "w", encoding="utf-8") as index_server:
            json.dump(new_index, index_server, indent=4, ensure_ascii=True)
        os.remove(self.client_path + "index.json")

    def generate_random_doc(self):
        raise NotImplementedError()

    def generate_keys(self):
        raise NotImplementedError()

    def request_search(self, word):
        raise NotImplementedError()
