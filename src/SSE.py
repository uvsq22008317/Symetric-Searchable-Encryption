import hashlib
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

class Encryptor:
    def __init__(self, key):
        self.key = get_random_bytes(16)

    def pad(self, data):
        # on pad pour que les données aient une longueur de 16 octets (besoin AES)
        padding_length = 16-(len(data)%16)
        return data + b'8' + ('0'*(padding_length-1)).encode()
        # b'<data>800000' pour que le total soit un multiple de 16 afin de pouvoir utiliser AES
    
    def unpad(self,data):
        return data[:-data[-1]]
        # on recupere la valeur correspondant au nombre d'octets ajouté et on enleve ce nombre de charactere

    def encrypt_document(self, content):
        cipher = AES.new(self.key, AES.MODE_CBC) # on chiffre le doc en AES mode CBC
        iv = cipher.iv
        encrypted_content = cipher.encrypt(self.pad(content.encode()))
        return bytes(iv) + encrypted_content

    def decrypt_document(self, encrypted_data):
        iv = encrypted_data[:16]
        encrypted_content = encrypted_data[16:]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        decrypted_content = self.unpad(cipher.decrypt(encrypted_content))
        return decrypted_content.decode()

    def encrypt_word(self, word):
        cipher = AES.new(self.key, AES.MODE_ECB) # on veut chiffrer le mot en mode ECB
        padded_word = self.pad(word.encode()) # on le pad avant pour qu'il fasse 16 octet
        return cipher.encrypt(padded_word)
