import os
import json
import shutil
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util import Counter
from Crypto.Util.Padding import pad, unpad
from config import PATHS, log_message, EXTENTIONS, ENCODED_EXTENTION
from utils.index import create_index, encrypt_index
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
    
def update_document(key, source, original_filename, new_content):
    log_message("INFO", f"Mise à jour du document {original_filename}")

    # verification que le fichier existe
    index_path = os.path.join(source, "index.json")
    if not os.path.exists(index_path):
        log_message("ERROR", f"Index non trouvé dans le dossier client")
        return False
    
    try :
        # recuperation de l'index
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)

        # verification que le fichier existe dans l'index
        document_exists = False
        for word,doc in index.items():  
            if original_filename in doc:
                document_exists = True
                break
        if not document_exists:
            log_message("ERROR", f"Document {original_filename} non trouvé dans l'index")
            return False
        
        # creation du fichier dans le dossier client
        doc_path = os.path.join(source, original_filename)
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        # on recree l'index complet
        encrypted_index_path = os.path.join(PATHS["server"], "encrypted_index.json")
        if os.path.exists(index_path):
            os.remove(index_path)
        if os.path.exists(encrypted_index_path):
            os.remove(encrypted_index_path)

        create_index(source)
        doc_name_map = encrypt_folder(key, source)
        encrypt_index(source, key, doc_name_map, regenerate=True)

        # deplace fichiers chiffrés vers serveur
        for enc_file in os.listdir(source):
            if enc_file.endswith(ENCODED_EXTENTION):
                src_path = os.path.join(source, enc_file)
                dest_path = os.path.join(PATHS["server"], enc_file)
                if os.path.exists(dest_path):
                    os.remove(dest_path) 
                shutil.move(src_path, dest_path)

        # deplace index vers serveur
        src_index = os.path.join(source, "encrypted_index.json")
        dest_index = os.path.join(PATHS["server"], "encrypted_index.json")
        shutil.move(src_index, dest_index)

        for file in os.listdir(source):
            if file.endswith(EXTENTIONS):
                os.remove(os.path.join(source, file))

        log_message("INFO", f"Document {original_filename} mis à jour avec succès")
        return True
    
    except Exception as e:
        log_message("ERROR", f"Erreur durant la mise à jour du document : {e}")
        return False