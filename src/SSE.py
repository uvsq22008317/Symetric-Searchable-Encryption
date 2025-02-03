import os
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes # génère des octets aléatoires 
import hashlib # pour hacher (sha256 => 256 bits, utile ou trop ?)

class SSE : 
    def __init__(self,key):
        self.key = hashlib.sha256(key.encode()).digest()
        self.index = {} # pour stocker les mots chiffrés (creer une classe independante ?)

    def pad(self, data):
        # on pad pour que les données aient une longueur de 16 octets (besoin AES)
        padding_length = 16-(len(data)%16)
        return data + (chr(padding_length)*padding_length).encode()
        # chaque charactere ajouté contient le nombre d'octets ajoutés
    
    def unpad(self,data):
        return data[:-data[-1]]
        # on recupere la valeur correspondant au nombre d'octets ajouté et on enleve ce nombre de charactere
    
    def encrypt_document(self, doc_id, content) :
        cipher = AES.new(self.key, AES.MODE_CBC) # on chiffre le doc en AES mode CBC
        iv = cipher.iv
        encrypted_content = cipher.encrypt(self.pad(content.encode()))
        self.store_encrypted_document(doc_id, iv+ encrypted_content)

    def store_encrypted_document(self, doc_id, encrypted_data):
        # contenu doc chiffré est stocké dans le repertoire 'Server'
        server_path = os.path.join(os.path.dirname(__file__), 'Server') 
        if not os.path.exists(server_path):  
            os.makedirs(server_path)
        with open(os.path.join(server_path, f'{doc_id}.enc'), 'wb') as file:
            file.write(encrypted_data)

    def create_index(self, doc_id, words):
        for word in words:
            encrypted_word = self.encrypt_word(word)
            if encrypted_word not in self.index:
                self.index[encrypted_word] = []
            self.index[encrypted_word].append(doc_id)

    def encrypt_word(self, word):
        cipher = AES.new(self.key, AES.MODE_ECB) # on veut chiffrer le mot en mode ECB
        padded_word = self.pad(word.encode()) # on le pad avant pour qu'il fasse 16 octet
        return cipher.encrypt(padded_word)

    def search(self, word):
        # on chiffre le mot cherché et on le compare à ceux dans l'index
        encrypted_word = self.encrypt_word(word)
        if encrypted_word in self.index:
            # on retetourne la liste des documents associés
            return self.index[encrypted_word]
        return []

    def decrypt_document(self, doc_id):
        server_path = os.path.join(os.path.dirname(__file__), 'Server')
        with open(os.path.join(server_path, f'{doc_id}.enc'), 'rb') as file:
            encrypted_data = file.read()
        iv = encrypted_data[:16]
        encrypted_content = encrypted_data[16:]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        decrypted_content = self.unpad(cipher.decrypt(encrypted_content))
        return decrypted_content.decode()


sse = SSE(key='secret_key')

# ajout document
sse.encrypt_document('doc1', "La facture du mois d'avril sera de 10000 euros.")
sse.create_index('doc1', ['facture', 'avril', 'euros'])

# recherche mot
result1 = sse.search('facture')
print(f'Documents contenant le mot "facture": {result1}')
result2 = sse.search('mars')
print(f'Documents contenant le mot "mars": {result2}')

# dechiffrement document
if result1:
    print(f'Contenu du document: {sse.decrypt_document(result1[0])}')
