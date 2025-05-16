
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

    def update_document(self, original_filename):
        log_message("INFO", f"Mise à jour du document {original_filename}")

        # Vérifie que le fichier existe dans la table de correspondance
        if original_filename not in self.doc_name_map:
            log_message("ERROR", f"Document {original_filename} non trouvé dans la table")
            return False
        encrypted_filename = self.doc_name_map[original_filename]
        if not self.get_file_from_server(encrypted_filename):
            return False

        encrypted_path = os.path.join(self.client_path, encrypted_filename)
        decrypted_content = self.decrypt_file(encrypted_path)
        
        if not decrypted_content:
            log_message("ERROR", "Échec du déchiffrement du fichier")
            return False

        log_message("INFO", f"Contenu actuel de {original_filename}:")
        print(decrypted_content.split(": ", 1)[1])  # affiche seulement le contenu
        
        log_message("INFO", "Entrez le nouveau contenu (appuyez sur Entrée pour garder l'actuel):")
        new_content = input("> ").strip()
        
        if not new_content:
            log_message("INFO", "Aucune modification apportée")
            os.remove(encrypted_path)
            return True

        # cree un nouveau fichier avec le contenu modifié
        new_file_path = os.path.join(self.client_path, original_filename)
        try:
            with open(new_file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        except Exception as e:
            log_message("ERROR", f"Erreur lors de l'écriture du nouveau contenu: {e}")
            return False
        
         # Chiffre le contenu
        nonce = get_random_bytes(8)
        ctr = Counter.new(64, prefix=nonce)
        cipher_content = AES.new(self.key, AES.MODE_CTR, counter=ctr)
        
        with open(new_file_path, 'r', encoding='utf-8') as f:
            plaintext = f.read().encode()
            
        encrypted_content = cipher_content.encrypt(pad(plaintext, 16, "iso7816"))

        old_encrypted = self.doc_name_map.get(original_filename)
        if old_encrypted:
            old_path = os.path.join(self.server_path, old_encrypted)
            try:
                if os.path.exists(old_path):
                    os.remove(old_path)
            except Exception as e:
                log_message("ERROR", f"Failed to delete old encrypted file: {e}")

        # Chiffre le nom
        iv = get_random_bytes(16)
        cipher_name = AES.new(self.key, AES.MODE_CBC, iv=iv)
        filename_clean = os.path.splitext(original_filename)[0].encode("utf-8")
        encrypted_name = cipher_name.encrypt(pad(filename_clean, 16, "iso7816"))

        # Création du nom du fichier encrypté
        encrypted_filename = encrypted_name.hex() + ENCODED_EXTENTION
        encrypted_path = os.path.join(PATHS["server"], encrypted_filename)
        
        # Sauvegarde du fichier chiffré
        with open(encrypted_path, 'wb') as f:
            name_len = len(encrypted_name).to_bytes(4, byteorder="big")
            f.write(nonce + iv + name_len + encrypted_name + encrypted_content)
        
        # Maj de la table de correspondance
        self.doc_name_map[original_filename] = encrypted_filename
        log_message("DEBUG", f"Fichier chiffré et ajouté au serveur: {encrypted_filename}")
    
        # Maj l'index chiffré
        self.add_to_index(original_filename, decrypted_content)
        self.encrypt_index()
        
        # Déplacer le nouvel index chiffré vers le serveur
        src = os.path.join(PATHS["client"], "encrypted_index.json")
        dst = os.path.join(PATHS["server"], "encrypted_index.json")
        shutil.move(src, dst)

        log_message("INFO", f"Document {original_filename} mis à jour avec succès")
        return True
    
    def formate_line(self, text):
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
                        for word in self.formate_line(line):
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
    
    def add_to_index(self, filename, old_content=None):
        log_message("INFO", f"Ajout/mise à jour du fichier {filename} dans l'index")
        
        # Chemins des fichiers
        file_path = os.path.join(self.client_path, filename)
        index_path = os.path.join(self.client_path, "index.json")
        
        # Vérifications
        if not os.path.isfile(file_path):
            log_message("ERROR", f"Le fichier {filename} n'existe pas dans le dossier client")
            return False
        
        if not filename.endswith(EXTENTIONS):
            log_message("ERROR", f"Le fichier {filename} n'a pas l'extension requise")
            return False
        
        try:
            # Charger l'index existant ou créer un nouveau si inexistant
            if os.path.isfile(index_path):
                with open(index_path, 'r', encoding='utf-8') as f:
                    index = json.load(f)
            else:
                index = {}
            
            # Lire le contenu du fichier
            with open(file_path, 'r', encoding='utf-8') as f:
                new_content = f.read()
            
             # Extraire les mots anciens et nouveaux
            old_words = set(self.formate_line(old_content)) if old_content else set()
            new_words = set(self.formate_line(new_content))
        
            # Mots à supprimer (présents avant mais plus maintenant)
            words_to_remove = old_words - new_words
            
            # Mots à ajouter (nouveaux ou déjà présents)
            words_to_add = new_words
            
            # supprimer les mots qui ne sont plus présents
            for word in words_to_remove:
                if word in index and filename in index[word]:
                    index[word].remove(filename)
                    if not index[word]:  # Supprimer le mot s'il n'a plus de fichiers
                        del index[word]
                    log_message("DEBUG", f"Mot supprimé de l'index: {word}")
            
            # Puis ajouter les nouveaux mots
            for word in words_to_add:
                if word not in index:
                    index[word] = []
                if filename not in index[word]:
                    index[word].append(filename)
                    log_message("DEBUG", f"Mot ajouté/mis à jour dans l'index: {word}")
            
            # Sauvegarder le nouvel index
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=4, ensure_ascii=False)
            
            log_message("DEBUG", f"Fichier {filename} ajouté/mis à jour dans l'index")
            return True
            
        except Exception as e:
            log_message("ERROR", f"Erreur lors de l'ajout/mise à jour du fichier {filename} dans l'index: {e}")
            return False

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
        
    def add_file_from_backup(self, filename):
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
                
            for word in self.formate_line(content):
                if word not in index:
                    index[word] = []
                if filename not in index[word]:
                    index[word].append(filename)
            
            # Sauvegarder le nouvel index
            with open(client_index_path, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=4, ensure_ascii=False)
            
            log_message("DEBUG", "Index client mis à jour")
            
            # Chiffrer le fichier et l'ajouter au serveur
            if filename not in self.doc_name_map:  # Si le fichier n'a pas déjà été chiffré
                # Chiffre le contenu
                nonce = get_random_bytes(8)
                ctr = Counter.new(64, prefix=nonce)
                cipher_content = AES.new(self.key, AES.MODE_CTR, counter=ctr)
                
                with open(backup_path, 'r', encoding='utf-8') as f:
                    plaintext = f.read().encode()
                    
                encrypted_content = cipher_content.encrypt(pad(plaintext, 16, "iso7816"))

                # Chiffre le nom
                iv = get_random_bytes(16)
                cipher_name = AES.new(self.key, AES.MODE_CBC, iv=iv)
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
                self.doc_name_map[filename] = encrypted_filename
                log_message("DEBUG", f"Fichier chiffré et ajouté au serveur: {encrypted_filename}")
            
            # Maj l'index chiffré
            self.encrypt_index()
            
            # Déplacer le nouvel index chiffré vers le serveur
            src = os.path.join(PATHS["client"], "encrypted_index.json")
            dst = os.path.join(PATHS["server"], "encrypted_index.json")
            shutil.move(src, dst)
            
            log_message("INFO", f"Fichier {filename} ajouté avec succès")
            return True
            
        except Exception as e:
            log_message("ERROR", f"Erreur lors de l'ajout du fichier {filename}: {e}")
            return False

    def remove_document(self, filename):
        log_message("INFO", f"Suppression du document {filename} en cours...")
        
        try:
            # Vérifie si le fichier existe dans la table
            if filename not in self.doc_name_map:
                log_message("ERROR", f"Le fichier {filename} n'existe pas dans la table")
                return False
            
            encrypted_name = self.doc_name_map[filename]
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
            del self.doc_name_map[filename]
            
            # Maj l'index chiffré
            self.encrypt_index()
            
            # Déplacer le nouvel index chiffré vers le serveur
            src = os.path.join(PATHS["client"], "encrypted_index.json")
            dst = os.path.join(PATHS["server"], "encrypted_index.json")
            shutil.move(src, dst)
            
            log_message("INFO", f"Document {filename} supprimé avec succès")
            return True
            
        except Exception as e:
            log_message("ERROR", f"Erreur lors de la suppression du document {filename}: {e}")
            return False