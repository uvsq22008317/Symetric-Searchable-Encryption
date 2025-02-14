import os
import sys
import random
import string

# Ajouter automatiquement le dossier parent au PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

from utils.logger import log_message
from Cryptodome.Random import get_random_bytes


# TESTING
import json

class Client:
    def __init__(self, name):
        log_message("INFO", f"Creation de l'instance du client {name}")
        self.name, self.key = name, get_random_bytes(16)
        self.path = os.path.join(config.CLIENTS_PATH, self.name)
        if not os.path.exists(self.path):
            os.makedirs(self.path)
            log_message("DEBUG", f"Dossier créé pour {self.name}")

    def get_name(self):
        log_message("DEBUG", f"Récupération du nom pour {self.name}")
        return self.name

    def get_key(self):
        log_message("DEBUG", f"Récupération de la clé pour {self.name}")
        return self.key

    def get_path(self):
        log_message("DEBUG", f"Récupération du chemin pour {self.name}")
        return self.path

    def __str__(self):
        raise NotImplementedError()

    def send_index(self):

        # Creation des chemins pour les index
        index_client_path = os.path.join(config.CLIENTS_PATH, "index.json")
        index_server_path = os.path.join(config.SERVER_PATH, "index.json")

        # Le fichier index.json du client existe-t-il ?
        if not os.path.exists(index_path):
            log_message("ERROR", f"Le fichier {index_path} n'existe pas.")
            return
        
        try:
            # Lire l'index depuis le client
            with open(index_client_path, "r", encoding="utf-8") as index_client:
                new_index = json.load(index_client)

            # Écrire l'index sur le serveur
            with open(server_index_path, "w", encoding="utf-8") as index_server:
                json.dump(new_index, index_server, indent=4, ensure_ascii=True)

            # Supprimer l'index local du client
            os.remove(index_client_path)
            log_message("INFO", f"L'index de {self.name} a été envoyé au serveur et a été supprimé localement.")

        except Exception as e:
            log_message("ERROR", f"Erreur lors de l'envoi de l'index : {e}")
            return

