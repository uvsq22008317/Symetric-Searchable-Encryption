import os
import json
import re
from config import EXTENTIONS, PATHS, log_message
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util import Counter
from Crypto.Util.Padding import pad, unpad
import hmac
import hashlib

def formate_line(text):
    # On sépare sur toute ponctuation ou espace
    raw_words = re.split(r"[^\w\-]+", text)

    # On filtre les chaînes vides
    return [word for word in raw_words if word]

def create_index(source):
    if not os.path.isdir(source):
        log_message("ERROR", f"Le chemin {source} n'est pas un dossier.")
        return

    log_message("INFO", f"Création de l'index...")
    index = {}

    for document in os.listdir(source):
        doc_path = os.path.join(source, document)
        if document.endswith(EXTENTIONS) and os.path.isfile(doc_path):
            log_message("DEBUG", f"Lecture du fichier {document}")
            with open(doc_path, "r", encoding="utf-8") as file:
                for line in file:
                    for word in formate_line(line):
                        if word not in index:
                            index[word] = []
                        if document not in index[word]:
                            index[word].append(document)

    # Écriture de l'index
    index_path = os.path.join(source, "index.json")
    try:
        with open(index_path, "w", encoding="utf-8") as json_file:
            json.dump(index, json_file, indent=4, ensure_ascii=False)
        log_message("DEBUG", f"Index créé avec succès dans : {index_path}")
    except Exception as e:
        log_message("ERROR", f"Erreur lors de la création de l'index : {e}")

def encrypt_index(source, key, doc_name_map, regenerate=False):
    log_message("INFO", "Chiffrement de l'index en cours...")

    index_path = os.path.join(source, "index.json")
    if not os.path.isfile(index_path):
        log_message("ERROR", f"L'index n'existe pas à cet emplacement : {index_path}")
        return

    # On charger l’index en clair
    try:
        with open(index_path, 'r', encoding='utf-8') as index_file:
            index = json.load(index_file)
    except Exception as e:
        log_message("ERROR", f"Erreur à l'ouverture de l'index : {e}")
        return

    # On remplacer les noms des documents de l'index par les noms chiffrées en CBC
    new_index = {}
    for word, doc_list in index.items():
        new_doc_list = []
        for doc in doc_list:
            if doc in doc_name_map:
                new_doc_list.append(doc_name_map[doc])
            else:
                log_message("WARNING", f"{doc} non trouvé dans la table de correspondance")
        new_index[word] = new_doc_list

    # On chiffre uniquement les mots et pas les noms de fichiers déjà chiffrées
    encrypted_index = {}
    for word, enc_doc_list in new_index.items():
        iv = get_random_bytes(16)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted_word = cipher.encrypt(pad(word.encode("utf-8"), 16, "iso7816")).hex()

        # C'est ici que tout se joue
        token = hashlib.pbkdf2_hmac("md5", word.encode('utf-8'), key, 5).hex()
        if regenerate:
            # Si on régénère complètement on peut recalculer tous les tokens
            encrypted_index[token] = enc_doc_list
        else:
            # Sinon on conserve la structure existante
            encrypted_index[token] = enc_doc_list

    # Sauvegarde de l’index chiffré
    try:
        encrypted_index_path = os.path.join(source, "encrypted_index.json")
        with open(encrypted_index_path, "w", encoding="utf-8") as f:
            json.dump(encrypted_index, f, indent=4, ensure_ascii=False)
        log_message("DEBUG", f"Index encrypté avec succès dans : {encrypted_index_path}")
        return encrypted_index
    except Exception as e:
        log_message("ERROR", f"Erreur lors de la sauvegarde de l'index encrypté : {e}")
        return None