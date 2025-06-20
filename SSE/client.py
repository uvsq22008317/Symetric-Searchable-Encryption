
import hashlib
import os
import json
import re
import shutil
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util import Counter
from Crypto.Util.Padding import pad, unpad
from SSE.config import EXTENTIONS, PATHS, ENCODED_EXTENTION, log_message


class Client:
    def __init__(self, key=None,client_path=None,server_path=None , backup_path=None):
        self.key = key or get_random_bytes(16)
        self.client_path =client_path or PATHS["client"]
        print(f"INIT : {self.client_path}")
        self.server_path = server_path or PATHS["server"]
        self.backup_path = backup_path or PATHS["backup"]
        self.ensure_directories()
        self.doc_name_map = {}

    def ensure_directories(self):
        # Crée les répertoires nécessaires si ils existent pas
        for path in [self.client_path, self.server_path, self.backup_path]:
            os.makedirs(path, exist_ok=True)

    def pad(self, data):
        return pad(data, 16, "iso7816")

    def unpad(self, data):
        return unpad(data, 16, "iso7816")

    def encrypt_folder(self):
        log_message("INFO", f"Encryption du dossier  {self.client_path}")
        
        if not os.path.isdir(self.client_path):
            log_message("ERROR", f"Erreur : le path source n'est pas un dossier : {self.client_path}")
            return {}

        self.doc_name_map = {}

        for document in os.listdir(self.client_path):
            if document.endswith(EXTENTIONS):
                try:
                    document_path = os.path.join(self.client_path, document)
                    log_message("DEBUG", f"Ouverture du fichier {document}")

                    with open(document_path, "r", encoding="utf-8") as file:
                        plaintext = file.read().encode()

                    # Chiffrement du contenu (mode CTR)
                    nonce = get_random_bytes(8)
                    ctr = Counter.new(64, prefix=nonce)
                    cipher_content = AES.new(self.key, AES.MODE_CTR, counter=ctr)
                    encrypted_content = cipher_content.encrypt(self.pad(plaintext))

                    # Chiffrement du nom (mode CBC)
                    iv = get_random_bytes(16)
                    cipher_name = AES.new(self.key, AES.MODE_CBC, iv=iv)
                    filename = os.path.splitext(document)[0].encode("utf-8")
                    encrypted_name = cipher_name.encrypt(self.pad(filename))

                    # Création du nom du fichier encrypté
                    encrypted_doc = encrypted_name.hex() + ENCODED_EXTENTION
                    encrypted_doc_path = os.path.join(self.client_path, encrypted_doc)

                    log_message("DEBUG", f"Ecriture du fichier encrypté : {encrypted_doc}")

                    with open(encrypted_doc_path, "wb") as f:
                        name_len = len(encrypted_name).to_bytes(4, byteorder="big")
                        # Format : nonce | iv | name_len | encrypted_name | encrypted_content
                        f.write(nonce + iv + name_len + encrypted_name + encrypted_content)

                    # Ajout dans la table de correspondance
                    self.doc_name_map[document] = encrypted_doc

                except Exception as e:
                    log_message("ERROR", f"Erreur durant l'encryption du fichier {document} : {e}")
                    continue

        log_message("DEBUG", f"Encryption du dossier {self.client_path} terminée")
        return self.doc_name_map
    
    def decrypt_file(self, encrypted_file_name):
        encrypted_file_path  = os.path.join(self.server_path, encrypted_file_name)
        log_message("DEBUG", f"Décryption du fichier {encrypted_file_path}")

        if not os.path.isfile(encrypted_file_path):
            log_message("ERROR", f"Erreur : le path source n'est pas un fichier : {encrypted_file_path}")
            return

        try:
            with open(encrypted_file_path, "rb") as f:
                nonce = f.read(8)
                iv = f.read(16)
                name_len = int.from_bytes(f.read(4), byteorder="big")
                encrypted_name = f.read(name_len)
                encrypted_content = f.read()

            # Déchiffrement du nom du fichier
            cipher_name = AES.new(self.key, AES.MODE_CBC, iv=iv)
            decrypted_name = self.unpad(cipher_name.decrypt(encrypted_name)).decode("utf-8")

            # Déchiffrement du contenu
            ctr = Counter.new(64, prefix=nonce)
            cipher_content = AES.new(self.key, AES.MODE_CTR, counter=ctr)
            decrypted_content = self.unpad(cipher_content.decrypt(encrypted_content)).decode("utf-8")

            return decrypted_name + ": " + decrypted_content

        except Exception as e:
            log_message("ERROR", f"Erreur durant la décryption du fichier {encrypted_file_path} : {e}")
            return
        
    def move_encrypted_files_to_server(self):
       # initialement fais dans le main mais pas du tout secure
        encrypted_files = [f for f in os.listdir(self.client_path) if f.endswith(ENCODED_EXTENTION)]

        # Si on génére aucun fichier dans Client logiquement il y a une erreur
        if not encrypted_files:
            log_message("ERROR", "Aucun fichier encrypté trouvé")
            return False
        
        # Déplacement des fichiers chiffrés vers le serveur
        for enc_file in encrypted_files:
            src_path = os.path.join(self.client_path, enc_file)
            dst_path = os.path.join(self.server_path, enc_file)

            for original_name, encrypted_name in self.doc_name_map.items():
                if encrypted_name == enc_file:
                    original_path = os.path.join(self.client_path, original_name)
                    backup_path = os.path.join(self.backup_path, original_name)

                    # Sauvegarde du fichier en clair dans le backup
                    if os.path.exists(original_path):
                        shutil.copy2(original_path, backup_path)
                        log_message("DEBUG", f"Copie du fichier clair dans le backup : {original_name}")
                    break

            # Sauvegarde du fichier chiffrée dans le serveur
            shutil.move(src_path, dst_path)
            log_message("DEBUG", f"Fichier déplacé vers le serveur : {enc_file}")

        return True
    
    def clean_client_folder(self):
        # iniatialement dans le main aussi mais toujours pas secure
        log_message("INFO", "Nettoyage du dossier client en cours...")
        for file in os.listdir(self.client_path):
            full_path = os.path.join(self.client_path, file)
            if os.path.isfile(full_path) and file not in ("index.json", "encrypted_index.json"):
                try:
                    os.remove(full_path)
                    log_message("DEBUG", f"Fichier supprimé : {file}")
                except Exception as e:
                    e
                    log_message("ERROR", f"Impossible de supprimer {file} : {e}")

    def formate_line(self, text):
        # On sépare sur toute ponctuation ou espace
        raw_words = re.split(r"[^\w\-]+", text)
        # On filtre les chaînes vides
        return [word for word in raw_words if word]

    def create_index(self):
        if not os.path.isdir(self.client_path):
            log_message("ERROR", f"Le chemin {self.client_path} n'est pas un dossier.")
            return

        log_message("INFO", f"Création de l'index...")
        index = {}

        for document in os.listdir(self.client_path):
            doc_path = os.path.join(self.client_path, document)
            if document.endswith(EXTENTIONS) and os.path.isfile(doc_path):
                log_message("DEBUG", f"Lecture du fichier {document}")
                with open(doc_path, "r", encoding="utf-8") as file:
                    for line in file:
                        for word in self.formate_line(line):
                            if word not in index:
                                index[word] = []
                            if document not in index[word]:
                                index[word].append(document)

        # Écriture de l'index
        index_path = os.path.join(self.client_path, "index.json")
        try:
            with open(index_path, "w", encoding="utf-8") as json_file:
                json.dump(index, json_file, indent=4, ensure_ascii=False)
            log_message("DEBUG", f"Index créé avec succès dans : {index_path}")
        except Exception as e:
            e
            log_message("ERROR", f"Erreur lors de la création de l'index : {e}")

    def encrypt_index(self, regenerate=False):
        log_message("INFO", "Chiffrement de l'index en cours...")

        index_path = os.path.join(self.client_path, "index.json")
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
                if doc in self.doc_name_map:
                    new_doc_list.append(self.doc_name_map[doc])
                else:
                    log_message("WARNING", f"{doc} non trouvé dans la table de correspondance")
            new_index[word] = new_doc_list

        # On chiffre uniquement les mots et pas les noms de fichiers déjà chiffrées
        encrypted_index = {}
        for word, enc_doc_list in new_index.items():
            token = hashlib.sha512(word.encode('utf-8')).hexdigest()
            encrypted_index[token] = enc_doc_list

        # Sauvegarde de l'index chiffré
        try:
            encrypted_index_path = os.path.join(self.client_path, "encrypted_index.json")
            with open(encrypted_index_path, "w", encoding="utf-8") as f:
                json.dump(encrypted_index, f, indent=4, ensure_ascii=False)
            log_message("DEBUG", f"Index encrypté avec succès dans : {encrypted_index_path}")
            return encrypted_index
        except Exception as e:
            log_message("ERROR", f"Erreur lors de la sauvegarde de l'index encrypté : {e}")
            return None
        
    def calculate_search_token(self, word):
        # Calcule le token de recherche sans exposer la clé au serveur
        try:
            return hashlib.sha512(word.encode("utf-8")).hexdigest()
        except Exception as e:
            log_message("ERROR", f"Erreur dans le calcul du token : {e}")
            return None
        
    def get_file_from_server(self, encrypted_filename):
        try:
            src_path = os.path.join(self.server_path, encrypted_filename)
            dst_path = os.path.join(self.client_path, encrypted_filename)
            
            if not os.path.exists(src_path):
                log_message("ERROR", f"Fichier {encrypted_filename} non trouvé sur le serveur")
                return False
                
            shutil.copy2(src_path, dst_path)
            log_message("DEBUG", f"Fichier {encrypted_filename} copié depuis le serveur")
            return True
        except Exception as e:
            log_message("ERROR", f"Erreur lors de la récupération du fichier: {e}")
            return False
        
    