
import hashlib
import hmac
import os
import json
import re
import shutil
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util import Counter
from Crypto.Util.Padding import pad, unpad
from config import EXTENTIONS, PATHS, log_message, ENCODED_EXTENTION


class Client:
    def __init__(self, key=None):
        self.key = key or get_random_bytes(16)
        self.client_path = PATHS["client"]
        self.server_path = PATHS["server"]
        self.backup_path = PATHS["backup"]
        self.ensure_directories()
        self.doc_name_map = {}
        self.doc_words_map = {}

    def ensure_directories(self):
        # Crée les répertoires nécessaires si ils existent pas
        for path in [self.client_path, self.server_path, self.backup_path]:
            os.makedirs(path, exist_ok=True)

    def pad(self, data):
        return pad(data, 16, "iso7816")

    def unpad(self, data):
        return unpad(data, 16, "iso7816")

    def encrypt_folder(self):
        log_message("INFO", f"Encryption du dossier {self.client_path}")
        
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
    
    def decrypt_file(self, encrypted_file_path):
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
                    log_message("ERROR", f"Impossible de supprimer {file} : {e}")

    def update_document(self, original_filename, new_content):
        log_message("INFO", f"Mise à jour du document {original_filename}")

        # Vérification que l'index existe
        index_path = os.path.join(self.client_path, "index.json")
        if not os.path.exists(index_path):
            log_message("ERROR", f"Index non trouvé dans le dossier client")
            return False
        
        try:
            # Vérification que le fichier existe dans l'index
            with open(index_path, "r", encoding="utf-8") as f:
                index = json.load(f)
            document_exists = any(original_filename in doc for word, doc in index.items())
            if not document_exists:
                log_message("ERROR", f"Document {original_filename} non trouvé dans l'index")
                return False
            
            # Création du fichier dans le dossier client
            doc_path = os.path.join(self.client_path, original_filename)
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            # Régénération complète de l'index
            encrypted_index_path = os.path.join(self.server_path, "encrypted_index.json")
            if os.path.exists(index_path):
                os.remove(index_path)
            if os.path.exists(encrypted_index_path):
                os.remove(encrypted_index_path)

            self.create_index()
            self.doc_name_map = self.encrypt_folder()
          #  self.encrypt_index(regenerate=True)

            # Déplacement des fichiers vers le serveur
            self.move_encrypted_files_to_server()

            # Déplacement de l'index vers le serveur
            src_index = os.path.join(self.client_path, "encrypted_index.json")
            dest_index = os.path.join(self.server_path, "encrypted_index.json")
            shutil.move(src_index, dest_index)

            # Nettoyage des fichiers originaux
            for file in os.listdir(self.client_path):
                if file.endswith(EXTENTIONS):
                    os.remove(os.path.join(self.client_path, file))

            log_message("INFO", f"Document {original_filename} mis à jour avec succès")
            return True
        
        except Exception as e:
            log_message("ERROR", f"Erreur durant la mise à jour du document : {e}")
            return False
    
    def format_line(self, text):
        # On sépare sur toute ponctuation ou espace
        raw_words = re.split(r"[^\w\-]+", text)
        # On filtre les chaînes vides
        return [word for word in raw_words if word]

    def prf(self,text):
        return hmac.new(self.key, text.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()
    
    def padForIndex(self,t,taille):
        return t.zfill(taille)

    def create_index(self):
        k =  get_random_bytes(16)
        if not os.path.isdir(self.client_path):
            log_message("ERROR", f"Le chemin {self.client_path} n'est pas un dossier.")
            return

        log_message("INFO", f"Création de l'index...")
        index = {}
    
        j=0
        
        mots_distincts = set()
        id_compteur = {}
        for document in os.listdir(self.client_path):
            doc_path = os.path.join(self.client_path, document)
            if document.endswith(EXTENTIONS) and os.path.isfile(doc_path):
                log_message("DEBUG", f"Lecture du fichier {document}")
                with open(doc_path, "r", encoding="utf-8") as file:
                    for line in file:
                        for word in self.format_line(line):
                            text = word + str(j)
                            l = self.prf(text)
                            mots_distincts.add(word)
                            if l not in index:
                                index[l] = []
                            if document not in index[l]:
                                index[l].append(document)
                            log_message("INFO",f"Indexing: word : {word} -> l : {l}- j :{j} -> document : {document}")
                            
                            if (document not in id_compteur):
                                id_compteur[document] = 0
                            id_compteur[document]+=1
                            if (word not in self.doc_words_map):
                                self.doc_words_map[word] = set()
                            self.doc_words_map[word].add(j)
                j+=1
                


        
          #ajout de valeurs factices
        log_message("INFO",f"AJOUT DE VALEUR FACTICE")
        # nombre de mots distinct 
        max = len(mots_distincts)
        # nbr de fois que chaque identifiant doit apparaitre dans l'index
        s = max * j

        s_prime = len(index)

        if (s_prime < s):
            i=0
            x=125
            y = max
            z = j
            for document in os.listdir(self.client_path):
                for l in range (1,max-id_compteur[document]):
                    text =  "0"*x+self.padForIndex(str(i),y)+self.padForIndex(str(l),y)
                    indice = self.prf(text)
                    #log_message("INFO",f"l'indice : {indice}")
                    if indice in index:
                        log_message("INFO",f"l'indice : {indice} existe deja")
                    index[indice] = [document]
                i+=1     
        
        # Écriture de l'index
        index_path = os.path.join(self.client_path, "index.json")
        try:
            with open(index_path, "w", encoding="utf-8") as json_file:
                json.dump(index, json_file, indent=4, ensure_ascii=False)
            log_message("DEBUG", f"Index créé avec succès dans : {index_path}")
        except Exception as e:
            log_message("ERROR", f"Erreur lors de la création de l'index : {e}")

    def trapdoor(self,word):
        trapdoor = []
        list_doc_index = self.doc_words_map[word]
        log_message("INFO",f" list_doc_index : {list_doc_index} associé au mot {word}")
        for j in (list_doc_index):
            text = word + str(j)
            l = self.prf(text)
            log_message("INFO",f" l : {l} -> le j : {j}")
            trapdoor.append(l)
        return trapdoor

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
        
        for word, enc_doc_list in index.items():
            log_message("INFO",f"INDEX :  word : {word}  en_doc_list {enc_doc_list}")

        # On remplacer les noms des documents de l'index par les noms chiffrées en CBC
        new_index = {}
        for word, doc_list in index.items():
            new_doc_list = []
            for doc in doc_list:
                if doc in self.doc_name_map:
                    new_doc_list.append(self.doc_name_map[doc])
                else:
                    log_message("WARNING", f"{doc} non trouvé dans la table de correspondance CLIENT")
            new_index[word] = new_doc_list

        # On chiffre uniquement les mots et pas les noms de fichiers déjà chiffrées
        encrypted_index = {}
        for word, enc_doc_list in new_index.items():
            """ Pas utilisé ?
            iv = get_random_bytes(16)
            cipher = AES.new(key, AES.MODE_CBC, iv)
            encrypted_word = cipher.encrypt(pad(word.encode("utf-8"), 16, "iso7816")).hex()
            """
            # C'est ici que tout se joue
            token = hashlib.pbkdf2_hmac("md5", word.encode('utf-8'), self.key, 5).hex()
            encrypted_index[token] = enc_doc_list
            log_message("INFO",f"ENCRYPTED WORD :{word} en doc list: {enc_doc_list}")

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
            return [ hashlib.pbkdf2_hmac("md5", t.encode('utf-8'), self.key, 5).hex() for t in  self.trapdoor(word) ]
        except Exception as e:
            log_message("ERROR", f"Erreur dans le calcul du token : {e}")
            return None