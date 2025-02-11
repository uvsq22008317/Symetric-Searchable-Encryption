import os
import json
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

CLIENTPATH = "./Client/"
SERVEURPATH = "./Serveur/"
extentions = (".txt")

class Encryptor:
    """
    On pad pour que les données aient une longueur de 16 octets
    Retourne b'<data>800000' (un multiple de 16 afin de pouvoir utiliser AES)
    """
    def pad(self, data):
        padding_length = 16-(len(data)%16)
        return data + b'8' + ('0'*(padding_length-1)).encode()
    
    """
    On recupere la valeur correspondant au nombre d'octets ajouté et 
    on enleve ce nombre de characteres à la fin du message
    """
    def unpad(self, data):
        return data[:-data[-1]]

    # Pas fini
    def encrypt_documents(self, key, client_path):
        for document in os.listdir(client_path):
            if document.endswith(extentions):
                cipher = AES.new(key, AES.MODE_CBC) #Cypher Block Chaining
                iv = cipher.iv
                with open(client_path + document, 'r', encoding='utf-8') as file:
                    encrypted_content = cipher.encrypt(self.pad(file.read().encode()))
                    encrypted_doc = client_path + os.path.splitext(document)[0] + '.enc'
                    with open(encrypted_doc, 'wb') as f:                                           
                        f.write(bytes(iv) + encrypted_content)                                       

    def decrypt_document(self, key, client_path, encrypted_data):
        with open(client_path + encrypted_data, 'rb') as f:
            iv = f.read(16)
            encrypted_content = f.read()
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted_content = self.unpad(cipher.decrypt(encrypted_content))
        return decrypted_content.decode()

    def encrypt_word(self, key, word):
        cipher = AES.new(self.key, AES.MODE_ECB)
        padded_word = self.pad(word.encode())
        return cipher.encrypt(padded_word)

    """
    On creer l'index en clair du dossier <client_path>
    """
    def create_index(self, key, client_path):
        if not os.path.exists(client_path):
            raise Exception("Le dossier {client_path} n'existe pas.")
        index = {}
        for document in os.listdir(client_path):
            if document.endswith(extentions):
                with open(client_path + document, 'r', encoding='utf-8') as file:  
                    for line in file:                                        
                        for word in line.split():                                          # ['The', 'question', 'isn', 't,', ...]
                            clean_word = word.strip(",.?!:;()[]{}\"'\n\t-")                # 'the', 'question', 'isn', 't'
                            if clean_word not in index:
                                index[clean_word] = []                                     # {'the': [], 'question': [], 'isn': [], 't': []}
                            if document not in index[clean_word]: 
                                index[clean_word].append(document)                         # {'the': ['doc1.txt'], 'question': ['doc1.txt'], ...}
        # Sauvegarde du dictionnaire en JSON
        with open(client_path + "/index.json", 'w', encoding='utf-8') as json_file:
            json.dump(index, json_file, ensure_ascii=True)

    def encrypt_index(self, key, index_path):
        with open(index_path, 'r', encoding='utf-8') as index_file:
            index = json.load(index_file)
        cipher = AES.new(key, AES.MODE_ECB)
        encrypted_index = {}
        for word, docs in index.items():
            encrypted_word = self.encrypt_word(key, word)
            encrypted_docs = [self.encrypt_word(key, doc) for doc in docs]
            encrypted_index[encrypted_word] = encrypted_docs
        return encrypted_index