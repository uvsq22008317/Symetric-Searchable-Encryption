import os
import json
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util import Counter

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
        reversed_data = data[::-1]
        padding_length = 0
        while reversed_data[padding_length] != '8'.encode('utf-8')[0]:
            padding_length += 1
        return data[:-(padding_length + 1)]

    def encrypt_documents(self, key, source, destination):
        for document in os.listdir(source):
            if document.endswith(".txt"):
                # 64 bits pour le nonce et 64 bits pour le ctr
                nonce = get_random_bytes(8)
                ctr = Counter.new(64, prefix=nonce) 
                cipher = AES.new(key, AES.MODE_CTR, counter=ctr)
                with open(source + document, 'r', encoding='utf-8') as file:
                    encrypted_content = cipher.encrypt(self.pad(file.read().encode()))
                    cipher2 = AES.new(key, AES.MODE_CBC)
                    iv = cipher2.iv
                    encrypted_name = cipher2.encrypt(self.pad(os.path.splitext(document)[0].encode()))
                    encrypted_doc = destination + encrypted_name.hex() + '.enc'
                    with open(encrypted_doc, 'wb') as f:    
                        f.write(bytes(nonce) + bytes(iv) + encrypted_content)                                       

    def decrypt_document(self, key, source):
        with open(source, 'rb') as f:
            nonce = f.read(8)
            iv = f.read(16)
            encrypted_content = f.read()
        ctr = Counter.new(64, prefix=nonce)
        cipher = AES.new(key, AES.MODE_CTR, counter=ctr)
        decrypted_content = self.unpad(cipher.decrypt(encrypted_content))
        return decrypted_content.decode('utf-8')

    def decrypt_documents(self, key, source):
        res = ""
        for document in os.listdir(source):
            if document.endswith(".enc"):
                decrypted_content = self.decrypt_document(key, source + document)
                decrypted_name = os.path.splitext(document)[0] + '.txt'
                res += decrypted_name + ": \"" + decrypted_content + "\"\n"
        return res

    def encrypt_word(self, key, word):
        cipher = AES.new(self.key, AES.MODE_ECB)
        padded_word = self.pad(word.encode())
        return cipher.encrypt(padded_word)

    """
    On creer l'index en clair du dossier <path> vers la <destination>
    client : Le client qui crée son index en fonction de ses documents
    """
    def create_index(self, client):
        path = client.get_path()
        key = client.get_key()
        if not os.path.exists(path):
            raise Exception("ERR: Le dossier Client n'existe pas")
        index = {}
        for document in os.listdir(path):
            if document.endswith(".txt"):
                with open(path + document, 'r', encoding='utf-8') as file:  
                    for line in file:                                        
                        for word in line.split():                                          # ['The', 'question', 'isn', 't,', ...]
                            clean_word = word.strip(",.?!:;()[]{}\"'\n\t-")                # 'the', 'question', 'isn', 't'
                            if clean_word not in index:
                                index[clean_word] = []                                     # {'the': [], 'question': [], 'isn': [], 't': []}
                            if document not in index[clean_word]: 
                                index[clean_word].append(document)                         # {'the': ['doc1.txt'], 'question': ['doc1.txt'], ...}
        # Sauvegarde du dictionnaire en JSON
        with open(path + "index.json", 'w', encoding='utf-8') as json_file:
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