import os
import json
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util import Counter

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

def pad_bit(data):
    padding_length = 16-(len(data)%16)
    return data + b'8' + ('0'*(padding_length-1)).encode()

def unpad_bit(data):
    reversed_data, padding_length = data[::-1].decode("utf-8"), 0
    while reversed_data[padding_length] != "8":
        padding_length += 1
    return data[:-(padding_length + 1)].decode('utf-8')

def encrypt_folder(key, source):
    config.log_message("INFO", f"Encryption du dossier {source}")
    # On verifie si le path source est bien un dossier
    if not os.path.isdir(source):
        config.log_message("ERROR", f"Erreur le path source n'est pas un dossier : {source}")
        return
    
    for document in os.listdir(source):
        if document.endswith(config.EXTENTIONS):
            try:
                # TODO : Ajout d'un suffix plus sécuritaire ? Qu'est ce qu'il se passe lorsque j'ai un counter plein ?
                # +---------+---------+
                # |  nonce  | counter |
                # +---------+---------+
                #  8 bytes  +  8 bytes  =  16 bytes
                # Ici on encrypte le contenu du document en utilisant le mode CTR
                nonce = get_random_bytes(8)
                ctr = Counter.new(64, prefix=nonce)
                cipher = AES.new(key, AES.MODE_CTR, counter=ctr)
                document_path = os.path.join(source, document)
                config.log_message("DEBUG", f"Ouverture du fichier {document}")
                with open(document_path, "r", encoding="utf-8") as file:
                    # Ici on encrypte le nom du document en utilisant le mode CBC (Cipher Block Chaining) + on a besoin du padding
                    encrypted_content = cipher.encrypt(pad_bit(file.read().encode()))
                    cipher2 = AES.new(key, AES.MODE_CBC, iv=get_random_bytes(16))
                    iv = cipher2.iv
                    # doc_1.txt deviendra Enc(k, doc_1).enc
                    encrypted_name = cipher2.encrypt(pad_bit(os.path.splitext(document)[0].encode("utf-8")))
                    encrypted_doc = encrypted_name.hex() + config.ENCODED_EXTENTION
                    encrypted_doc_path = os.path.join(source, encrypted_doc)
                    config.log_message("DEBUG", f"Ecriture du fichier {document} encrypté en {encrypted_doc}")
                    with open(encrypted_doc_path, "wb") as f:
                        # On stocke le nonce pour le contenu, l'iv du nom et le contenu encrypté dans le fichier
                        f.write(bytes(nonce) + bytes(iv) + encrypted_content)  
            except Exception as e:
                config.log_message("ERROR", f"Erreur lors de l'ouverture/écriture du fichier lors de l'encryption {document} : {e}")
                return                 
    config.log_message("DEBUG", f"Encryption du dossier {source} terminée")        

def decrypt_file(key, source):
    config.log_message("INFO", f"Decryption du fichier {source} en cours")
    # On verifie si le path source est bien un fichier
    if not os.path.isfile(source):
        config.log_message("ERROR", f"Erreur le path source n'est pas un fichier : {source}")
        return
    try:
        config.log_message("DEBUG", f"Ecriture du fichier {source}")
        with open(source, "rb") as f:
            nonce = f.read(8)
            iv = f.read(16)
            encrypted_content = f.read()
        ctr = Counter.new(64, prefix=nonce)
        cipher = AES.new(key, AES.MODE_CTR, counter=ctr)
        decrypted_content = cipher.decrypt(encrypted_content)
        config.log_message("DEBUG", f"Decryption du fichier {source} terminée")        
        return nonce, iv, decrypted_content
    except Exception as e:
        config.log_message("ERROR", f"Erreur dans l'écriture du fichier {source}")
        return

def decrypt_folder(key, source):
    config.log_message("INFO", f"Decryption du dossier {source}")
    if not os.path.isdir(source):
        config.log_message("ERROR", f"Erreur le path source n'est pas un dossier : {source}")
        return
    try:
        res = "\n**Decryption**"
        for document in os.listdir(source):
            if document.endswith(config.ENCODED_EXTENTION):
                encrypted_doc_path = os.path.join(source, document)
                nonce, iv, decrypted_content = decrypt_file(key, encrypted_doc_path)
                cipher = AES.new(key, AES.MODE_CBC, iv=iv)
                encrypted_name = bytes.fromhex(os.path.splitext(document)[0])
                decrypted_name = unpad_bit(cipher.decrypt(encrypted_name))
                res += "\n" + decrypted_name + ": \"" + unpad_bit(decrypted_content) + "\""
        return res + "\n**Decryption**\n"
    except Exception as e:
        config.log_message("ERROR", f"Erreur lors de la décryption du dossier {source} : {e}")
        return