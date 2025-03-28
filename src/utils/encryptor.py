import os
import json
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util import Counter
from Crypto.Util.Padding import pad, unpad
from config import PATHS, log_message, EXTENTIONS, ENCODED_EXTENTION
import hmac
import hashlib

def encrypt_folder(key, source):
    log_message("INFO", f"Encryption du dossier {source}")

    if not os.path.isdir(source):
        log_message("ERROR", f"Erreur : le path source n'est pas un dossier : {source}")
        return {}

    doc_name_map = {}

    for document in os.listdir(source):
        if document.endswith(EXTENTIONS):
            try:
                document_path = os.path.join(source, document)
                log_message("DEBUG", f"Ouverture du fichier {document}")

                with open(document_path, "r", encoding="utf-8") as file:
                    plaintext = file.read().encode()

                # Chiffrement du contenu
                nonce = get_random_bytes(8)
                ctr = Counter.new(64, prefix=nonce)
                cipher_content = AES.new(key, AES.MODE_CTR, counter=ctr)
                encrypted_content = cipher_content.encrypt(pad(plaintext, 16, "iso7816"))

                # Chiffrement du nom
                iv = get_random_bytes(16)
                cipher_name = AES.new(key, AES.MODE_CBC, iv=iv)
                filename = os.path.splitext(document)[0].encode("utf-8")
                encrypted_name = cipher_name.encrypt(pad(filename, 16, "iso7816"))

                # Création du nom du fichier encrypté
                encrypted_doc = encrypted_name.hex() + ENCODED_EXTENTION
                encrypted_doc_path = os.path.join(source, encrypted_doc)

                log_message("DEBUG", f"Ecriture du fichier encrypté : {encrypted_doc}")

                with open(encrypted_doc_path, "wb") as f:
                    name_len = len(encrypted_name).to_bytes(4, byteorder="big")
                    # Format : nonce | iv | name_len | encrypted_name | encrypted_content
                    f.write(nonce + iv + name_len + encrypted_name + encrypted_content)

                # Ajout dans la table de correspondance
                doc_name_map[document] = encrypted_doc

            except Exception as e:
                log_message("ERROR", f"Erreur durant l'encryption du fichier {document} : {e}")
                continue

    log_message("DEBUG", f"Encryption du dossier {source} terminée")
    return doc_name_map

def decrypt_file(key, source):
    log_message("DEBUG", f"Décryption du fichier {source}")

    if not os.path.isfile(source):
        log_message("ERROR", f"Erreur : le path source n'est pas un fichier : {source}")
        return

    try:
        with open(source, "rb") as f:
            nonce = f.read(8)
            iv = f.read(16)
            name_len = int.from_bytes(f.read(4), byteorder="big")
            encrypted_name = f.read(name_len)
            encrypted_content = f.read()

        # Déchiffrement du nom du fichier
        cipher_name = AES.new(key, AES.MODE_CBC, iv=iv)
        decrypted_name = unpad(cipher_name.decrypt(encrypted_name), 16, "iso7816").decode("utf-8")

        # Déchiffrement du contenu
        ctr = Counter.new(64, prefix=nonce)
        cipher_content = AES.new(key, AES.MODE_CTR, counter=ctr)
        decrypted_content = unpad(cipher_content.decrypt(encrypted_content), 16, "iso7816").decode("utf-8")

        return decrypted_name + ": " + decrypted_content

    except Exception as e:
        log_message("ERROR", f"Erreur durant la décryption du fichier {source} : {e}")
        return

def search_word(word, key):
    try:
        encrypted_index_path = os.path.join(PATHS["server"], "encrypted_index.json")
        with open(encrypted_index_path, 'r', encoding='utf-8') as f:
            encrypted_index = json.load(f)
    except Exception as e:
        log_message("ERROR", f"Erreur à l\'ouverture de l\'index : {e}")
        return []

    try:
        token = hashlib.pbkdf2_hmac("md5", word.encode('utf-8'), key, 5).hex()
        return encrypted_index.get(token, [])
    except Exception as e:
        log_message("ERROR", f"Erreur pendant la recherche du mot : {e}")
        return []