import os
import json

class Serveur:
    def __init__(self, encryptor, server_path="./Serveur/"):
        self.encryptor = encryptor                                       # L'Instance du Client
        self.client_path = encryptor.client_path                         # ./Client/
        self.server_path = server_path                                   # ./Serveur/
        self.index_path = os.path.join(self.server_path, 'index.json')   # ./Serveur/index.json
        if not os.path.exists(self.server_path):
            os.makedirs(self.server_path)
        self.load_index()

    # A partir de "./Serveur/index.json", cette fonction crée self.index
    # Print : self.index = {Enc(w^i) : ['tmp1.enc'], Enc(w^i+1) : ['tmp1.enc', 'tmp2.enc']}
    # /!\ type(Enc(w^i)) = bytes/octets
    def load_index(self):
        if os.path.exists(self.index_path):
            with open(self.index_path, 'r') as file:
                self.index = {bytes.fromhex(k): v for k, v in json.load(file).items()}

    # A partir de self.index, on va creer le fichier "index.json"
    #
    #
    def create_index(self, doc_id, words):
        # Encrypt words and associates them with the doc where they are
        for word in words:
            encrypted_word = self.encryptor.encrypt_word(word)
            if encrypted_word not in self.index:
                self.index[encrypted_word] = [] # Init doc list if the word not exist
            self.index[encrypted_word].append(doc_id) # Associate word with doc

    # Pour un mot w^i nommé word, cherche 
    #
    #
    def search(self, word):
        # Find doc containing the word
        encrypted_word = self.encryptor.encrypt_word(word)
        if os.path.exists(self.index_path):
            with open(self.index_path, 'r') as file:
                index_data = json.load(file)  # Load the JSON data
                matching_files = []
                for filename in index_data.get(encrypted_word.hex(), []):
                    source_path = os.path.join(self.server_path, filename)
                    dest_path = os.path.join(self.client_path, filename)
                    with open(source_path, "rb") as source, open(dest_path, "wb") as dest:
                        dest.write(source.read())
                    matching_files.append(filename)
                return matching_files
                    

    def get_server_path(self):
        return self.server_path
