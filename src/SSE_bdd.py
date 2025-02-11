import os
import json

CLIENTPATH = "./Client/"
SERVEURPATH = "./Serveur/"
INDEXPATH = "./Serveur/index.json"

class Database:
    def __init__(self, user_id, encryptor):
        self.user_id = user_id
        self.encryptor = encryptor
        self.server_path, self.index_path = SERVEURPATH, INDEXPATH
        self.index = {}

        if not os.path.exists(self.server_path):
            os.makedirs(self.server_path)
            raise Exception("Le dossier Serveur n'existait pas, il a été crée.")
        self.load_index()

    """
    Save the self.index dict to a file + convert keys to hexa
    """
    def save_index(self):
        with open(self.index_path, 'w') as file:
            json.dump({k.hex(): v for k, v in self.index.items()}, file)

    """
    Load index from file (convert hexa to binary)
    """
    def load_index(self):
        if os.path.exists(self.index_path):
            with open(self.index_path, 'r') as file:
                self.index = {bytes.fromhex(k): v for k, v in json.load(file).items()}

    def store_encrypted_document(self, doc_id, encrypted_data):
        # Encrypted doc content is stored in the user's directory
        file_path = os.path.join(self.server_path, f'{doc_id}.enc')
        with open(file_path, 'wb') as file:
            file.write(encrypted_data)

    def recover_encrypted_document(self, doc_id):
        # Recover encrypted doc from user's folder
        file_path = os.path.join(self.server_path, f'{doc_id}.enc')
        if os.path.exists(file_path):
            with open(file_path, 'rb') as file:
                return file.read()
        return None

    def create_index(self, doc_id, words):
        # Encrypt words and associates them with the doc where they are
        
        for word in words:
            encrypted_word = self.encryptor.encrypt_word(word)
            if encrypted_word not in self.index:
                self.index[encrypted_word] = [] # Init doc list if the word not exist
            self.index[encrypted_word].append(doc_id) # Associate word with doc

        self.save_index()

    def search(self, word):
        # Find doc containing the word
        encrypted_word = self.encryptor.encrypt_word(word)
        return self.index.get(encrypted_word, []) # Return list of doc for the word
