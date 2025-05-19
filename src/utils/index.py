import os
import json
import re
from config import EXTENTIONS, ENCODED_EXTENTION, PATHS, log_message
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util import Counter
from Crypto.Util.Padding import pad, unpad
import hmac
import hashlib
import shutil

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

def encrypt_index(source, key, doc_name_map):
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
        token = hashlib.pbkdf2_hmac("sha256", word.encode('utf-8'), key, 600_000).hex()
        encrypted_index[token] = enc_doc_list

    # Sauvegarde de l’index chiffré
    try:
        encrypted_index_path = os.path.join(source, "encrypted_index.json")
        with open(encrypted_index_path, "w", encoding="utf-8") as f:
            json.dump(encrypted_index, f, indent=4, ensure_ascii=False)
        log_message("DEBUG", f"Index encrypté avec succès dans : {encrypted_index_path}")
    except Exception as e:
        log_message("ERROR", f"Erreur lors de la sauvegarde de l'index encrypté : {e}")


def add_file_from_backup(key, filename, doc_name_map):
    log_message("INFO", f"Traitement de {filename} du backup")
    
    # Chemins des fichiers
    backup_path = os.path.join(PATHS["backup"], filename)
    client_index_path = os.path.join(PATHS["client"], "index.json")
    server_index_path = os.path.join(PATHS["server"], "encrypted_index.json")
    
    # Vérifie que le fichier existe dans le backup
    if not os.path.isfile(backup_path):
        log_message("ERROR", f"Le fichier {filename} n'existe pas dans le backup")
        return False
    
    # Vérifieque l'index existe
    if not os.path.isfile(client_index_path):
        log_message("ERROR", "L'index client n'existe pas")
        return False
    
    try:
        # Charger l'index existant
        with open(client_index_path, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        # Lire le fichier et maj l'index
        with open(backup_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        for word in formate_line(content):
            if word not in index:
                index[word] = []
            if filename not in index[word]:
                index[word].append(filename)
        
        # Sauvegarder le nouvel index
        with open(client_index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=4, ensure_ascii=False)
        
        log_message("DEBUG", "Index client mis à jour")
        
        # Chiffrer le fichier et l'ajouter au serveur
        if filename not in doc_name_map:  # Si le fichier n'a pas déjà été chiffré
            # Chiffre le contenu
            nonce = get_random_bytes(8)
            ctr = Counter.new(64, prefix=nonce)
            cipher_content = AES.new(key, AES.MODE_CTR, counter=ctr)
            
            with open(backup_path, 'r', encoding='utf-8') as f:
                plaintext = f.read().encode()
                
            encrypted_content = cipher_content.encrypt(pad(plaintext, 16, "iso7816"))

            # Chiffre le nom
            iv = get_random_bytes(16)
            cipher_name = AES.new(key, AES.MODE_CBC, iv=iv)
            filename_clean = os.path.splitext(filename)[0].encode("utf-8")
            encrypted_name = cipher_name.encrypt(pad(filename_clean, 16, "iso7816"))

            # Création du nom du fichier encrypté
            encrypted_filename = encrypted_name.hex() + ENCODED_EXTENTION
            encrypted_path = os.path.join(PATHS["server"], encrypted_filename)
            
            # Sauvegarde du fichier chiffré
            with open(encrypted_path, 'wb') as f:
                name_len = len(encrypted_name).to_bytes(4, byteorder="big")
                f.write(nonce + iv + name_len + encrypted_name + encrypted_content)
            
            # Maj de la table de correspondance
            doc_name_map[filename] = encrypted_filename
            log_message("DEBUG", f"Fichier chiffré et ajouté au serveur: {encrypted_filename}")
        
        # Maj l'index chiffré
        encrypt_index(PATHS["client"], key, doc_name_map)
        
        # Déplacer le nouvel index chiffré vers le serveur
        src = os.path.join(PATHS["client"], "encrypted_index.json")
        dst = os.path.join(PATHS["server"], "encrypted_index.json")
        shutil.move(src, dst)
        
        log_message("INFO", f"Fichier {filename} ajouté avec succès")
        return True
        
    except Exception as e:
        log_message("ERROR", f"Erreur lors de l'ajout du fichier {filename}: {e}")
        return False

def remove_document(key, filename, doc_name_map):
    log_message("INFO", f"Suppression du document {filename} en cours...")
    
    try:
        # Vérifie si le fichier existe dans la table
        if filename not in doc_name_map:
            log_message("ERROR", f"Le fichier {filename} n'existe pas dans la table")
            return False
        
        encrypted_name = doc_name_map[filename]
        encrypted_path = os.path.join(PATHS["server"], encrypted_name)
        backup_path = os.path.join(PATHS["backup"], filename)
        
        # Charger l'index clair
        index_path = os.path.join(PATHS["client"], "index.json")
        if not os.path.exists(index_path):
            log_message("ERROR", "L'index clair n'existe pas")
            return False
            
        with open(index_path, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        # Maj l'index
        updated_index = {}
        for word, files in index.items():
            if filename in files:
                files.remove(filename)
            if files:  # Garder que les mots qui ont encore des fichiers
                updated_index[word] = files
        
        # Sauvegarder le nouvel index
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(updated_index, f, indent=4, ensure_ascii=False)
        
        # Supprimer les fichiers
        if os.path.exists(encrypted_path):
            os.remove(encrypted_path)
            log_message("DEBUG", f"Fichier chiffré supprimé: {encrypted_name}")
        
        if os.path.exists(backup_path):
            os.remove(backup_path)
            log_message("DEBUG", f"Fichier backup supprimé: {filename}")
        
        # Maj la table
        del doc_name_map[filename]
        
        # Maj l'index chiffré
        encrypt_index(PATHS["client"], key, doc_name_map)
        
        # Déplacer le nouvel index chiffré vers le serveur
        src = os.path.join(PATHS["client"], "encrypted_index.json")
        dst = os.path.join(PATHS["server"], "encrypted_index.json")
        shutil.move(src, dst)
        
        log_message("INFO", f"Document {filename} supprimé avec succès")
        return True
        
    except Exception as e:
        log_message("ERROR", f"Erreur lors de la suppression du document {filename}: {e}")
        return False