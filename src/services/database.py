import os
import json

class Database:
    def __init__(self, path):
        self.path = path                # "./src/Serveur/"
        self.index, self.index_path = {}, os.path.join(self.path, 'index.json')

        if not os.path.exists(self.path):
            os.makedirs(self.path)

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
        else:
            print("Serveur: Index non trouvé")

    def store_encrypted_document(self, doc_id, encrypted_data):
        # Encrypted doc content is stored in the user's directory
        file_path = os.path.join(self.server_path, f'{doc_id}.enc')
        with open(file_path, 'wb') as file:
            file.write(encrypted_data)

    def recover_encrypted_document(self, doc_id):
        raise NotImplementedError("Not yet")


    def search(self, word):
        # Find doc containing the word
        encrypted_word = self.encryptor.encrypt_word(word)
        return self.index.get(encrypted_word, []) # Return list of doc for the word
