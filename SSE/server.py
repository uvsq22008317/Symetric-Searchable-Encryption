import os
import json
import hmac
import hashlib
import shutil
from SSE.config import PATHS ,log_message

class Server :
    def __init__(self, client,server_path=None):
        self.client = client
        self.server_path = server_path or  PATHS["server"]
        self.encrypted_index_path = os.path.join(self.server_path, "encrypted_index.json")
        self.load_index()

    def load_index(self):
        if os.path.exists(self.encrypted_index_path):
            try:
                with open(self.encrypted_index_path, 'r', encoding='utf-8') as f:
                    self.encrypted_index = json.load(f)
            except Exception as e:
                log_message("ERROR", f"Erreur à l\'ouverture de l\'index : {e}")
                self.encrypted_index = {}
        else:
            self.encrypted_index = {}

    def search_word(self, token):
        # Recherche par token pré-calculé par le client
        try:
            return self.encrypted_index.get(token, [])
        except Exception as e:
            log_message("ERROR", f"Erreur pendant la recherche du mot : {e}")
            return []
        
    def transfer_files_to_client(self, encrypted_files):
        # on transfère temporairement les fichiers chiffrés vers le client pour les déchiffrer
        temp_files = []

        for enc_file in encrypted_files:
            server_path = os.path.join(self.server_path, enc_file)
            client_path = os.path.join(self.client.client_path, enc_file)

            if os.path.exists(server_path):
                # Copier vers le Client
                shutil.copy2(server_path, client_path)
                temp_files.append(client_path)
                log_message("DEBUG", f"Fichier transféré temporairement : {enc_file}")
            #else:
                log_message("WARNING", f"Fichier non trouvé sur le serveur : {server_path}")
        
        return temp_files
    
    def cleanup_temp_files(self, temp_files):
        # Nettoie les fichiers temporaires apres leur utilisation
        for file in temp_files:
            try:
                os.remove(file)
                log_message("DEBUG", f"Fichier temporaire supprimé : {os.path.basename(file)}")
            except Exception as e:
                e
                log_message("ERROR", f"Erreur de suppression du fichier {file} : {e}")