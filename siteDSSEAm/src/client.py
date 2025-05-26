
import base64
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
        
        self.client_path = PATHS["client"]
        self.server_path = PATHS["server"]
        self.backup_path = PATHS["backup"]
        self.ensure_directories()
        self.doc_name_map = {}
        self.doc_words_map = {}
        self.doc_encryp_info = {}
        self.encrypted_index = []

    def ensure_directories(self):
        # Crée les répertoires nécessaires si ils existent pas
        for path in [self.client_path, self.server_path, self.backup_path]:
            os.makedirs(path, exist_ok=True)

    def pad(self, data):
        return pad(data, 16, "iso7816")

    def unpad(self, data):
        return unpad(data, 16, "iso7816")

    def encrypt_folder(self,list_doc,key):
        encrypted_docs_list = []
        for document in list_doc:
            # Chiffrement du contenu (mode CTR)
            nonce = get_random_bytes(8)
            ctr = Counter.new(64, prefix=nonce)
            cipher_content = AES.new(key, AES.MODE_CTR, counter=ctr)
            text = document["text"]
            encrypted_content = cipher_content.encrypt(self.pad(text.encode("utf-8")))

            # Chiffrement du nom (mode CBC)
            iv = get_random_bytes(16)
            cipher_name = AES.new(key, AES.MODE_CBC, iv=iv)
            name = document["name"]

             # Création du nom du fichier encrypté
            encrypted_name = cipher_name.encrypt(self.pad(name.encode("utf-8")))

           #Ajout info utile 
            info = {"nonce": base64.b64encode(nonce).decode() , "iv": base64.b64encode(iv).decode() }
            self.doc_encryp_info[encrypted_name.hex()] = info
            encrypted_doc = encrypted_name.hex() + ENCODED_EXTENTION

            log_message("DEBUG", f"Ecriture du fichier encrypté : {encrypted_doc}")

            document = {"name": encrypted_name.hex() , "text": encrypted_content.hex()}
            encrypted_docs_list.append(document)

            
            # Ajout dans la table de correspondance ICI PB
            self.doc_name_map[name] = encrypted_name.hex()

            log_message("DEBUG", f"Encryption du dossier {self.client_path} terminée")
        return encrypted_docs_list ,  self.doc_encryp_info
    

    def decrypt_file_name(self,encrypted_doc,doc_encryp_info,key):
            encrypted_name = encrypted_doc["doc"][0]
            print(f" doc encrypt info : {doc_encryp_info}")
            nonce = base64.b64decode(doc_encryp_info[encrypted_name]["nonce"])
            iv =base64.b64decode(doc_encryp_info[encrypted_name]["iv"])
            # Déchiffrement du nom du fichier
            cipher_name = AES.new(key, AES.MODE_CBC, iv=iv)
            decrypted_name = self.unpad(cipher_name.decrypt(encrypted_name)).decode("utf-8")
            return decrypted_name

    def decrypt_file(self, encrypted_doc,doc_encryp_info,key):
            
            #print(f" encrypted doc : {encrypted_doc}")
            
            encrypted_name = encrypted_doc[0]["name"]
            encrypted_name_bytes = bytes.fromhex(encrypted_name)
            encrypted_content = encrypted_doc[0]["text"]
            encrypted_content_bytes  = bytes.fromhex(encrypted_content)

            nonce = base64.b64decode(doc_encryp_info[encrypted_name]["nonce"])
            iv = base64.b64decode(doc_encryp_info[encrypted_name]["iv"])

            # Déchiffrement du nom du fichier
            cipher_name = AES.new(key, AES.MODE_CBC, iv=iv)
            #print(f"encrypted name : {encrypted_name}")
            decrypted_name = self.unpad(cipher_name.decrypt(encrypted_name_bytes)).decode("utf-8")

            # Déchiffrement du contenu
            ctr = Counter.new(64, prefix=nonce)
            cipher_content = AES.new(key, AES.MODE_CTR, counter=ctr)
            decrypted_content = self.unpad(cipher_content.decrypt(encrypted_content_bytes)).decode("utf-8")
            document = {}
            document["name"] = decrypted_name
            document["content"] = decrypted_content
            return document

        
        
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

    def prp(self,text,key):
        cipher = AES.new(key, AES.MODE_ECB)
        return cipher.encrypt(pad(text.encode('utf-8'), AES.block_size) ).hex()
        #return hmac.new(key, text.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()
    
    def padForIndex(self,t,taille):
        return t.zfill(taille)

    def create_index(self,documents,key):
        k =  get_random_bytes(16)

        log_message("INFO", f"Création de l'index...")
        index = {}
        j=0
        mots_distincts = set()
        id_compteur = {}
        for document in documents:
                        for word in self.format_line(document["text"]):
                            text = word + str(j)
                            l = self.prp(text,key)
                            mots_distincts.add(word)
                            if l not in index:
                                index[l] = []
                            if document not in index[l]:
                                index[l].append(document)
                            #log_message("INFO",f"Indexing: word : {word} -> l : {l}- j :{j} -> document : {document}")
                            
                            if (document["name"] not in id_compteur):
                                id_compteur[document["name"]] = 0
                            id_compteur[document["name"]]+=1
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
            for document in documents:
                for l in range (1,max-id_compteur[document["name"]]):
                    text =  "0"*x+self.padForIndex(str(i),y)+self.padForIndex(str(l),y)
                    indice = self.prp(text,key)
                    #log_message("INFO",f"l'indice : {indice}")
                    if indice in index:
                        log_message("INFO",f"l'indice : {indice} existe deja")
                    index[indice] = [document]
                i+=1     
        return index , self.doc_words_map

    def trapdoor(self,word,doc_words_map,key):
        trapdoor = []
        list_doc_index = doc_words_map[word]
        for j in (list_doc_index):
            text = word + str(j)
            l = self.prp(text,key)
            trapdoor.append(l)
        return trapdoor

    def encrypt_index(self,index,key, regenerate=False):
        log_message("INFO", "Chiffrement de l'index en cours...")    
        # On remplacer les noms des documents de l'index par les noms chiffrées en CBC
        new_index = {}
        for word, doc_list in index.items():
            new_doc_list = []
            for doc in doc_list:
                if doc["name"] in self.doc_name_map:
                    new_doc_list.append(self.doc_name_map[doc["name"]])
                else:
                    log_message("WARNING", f"{doc} non trouvé dans la table de correspondance CLIENT")
                docu = {"token": word , "doc": new_doc_list}
                self.encrypted_index.append(docu)
        # On chiffre uniquement les mots et pas les noms de fichiers déjà chiffrées
        return  self.encrypted_index
        
    def calculate_search_token(self, word,doc_words_map,key):
        # Calcule le token de recherche sans exposer la clé au serveur
        try:
            return self.trapdoor(word,doc_words_map ,key)
        except Exception as e:
            log_message("ERROR", f"Erreur dans le calcul du token : {e}")
            return None