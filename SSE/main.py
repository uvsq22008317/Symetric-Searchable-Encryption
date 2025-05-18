
import json
import os
import shutil
import sys
import time

from SSE.client import Client
from SSE.server import Server
from SSE.file_generator import FileGenerator
from SSE.config import EXTENTIONS, PATHS, log_message, remove_residual_files , FRUITS_LIST

import matplotlib.pyplot as plt

def main():
    # Initialisation de l'environnement
    remove_residual_files(PATHS["client"])
    remove_residual_files(PATHS["server"])
    remove_residual_files(PATHS["backup"])

    # génération de fichiers aléatoires
    FileGenerator.generate_random_file(PATHS["client"], num_files=10)

    # Création du client
    client = Client()

    # Création de l'index
    client.create_index()

    # Chiffrement des documents
    doc_name_map = client.encrypt_folder()

    # Déplacement des fichiers vers le serveur
    if not client.move_encrypted_files_to_server():
        sys.exit(1)

    # Chiffrement de l'index
    client.encrypt_index()

    # Déplacement de l'index vers le serveur
    src_index = os.path.join(PATHS["client"], "encrypted_index.json")
    dst_index = os.path.join(PATHS["server"], "encrypted_index.json")
    shutil.move(src_index, dst_index)

    # Nettoyage du dossier client
    client.clean_client_folder()

    # Création du serveur
    server = Server(client)

    # Interface utilisateur
    log_message("INFO", "Environnement Client/Serveur prêt !")
    log_message("INFO", "Recherche dans index chiffré")
    log_message("INFO", "Donnez le mot que vous cherchez ou quittez avec 'exit'")

    while True:
        word = input("> ").strip()
        if word.lower() in ["exit", "quit", "break", "q", "stop", "quitter"]:
            log_message("INFO", "Le Client a quitté la connexion")
            break

        if not word:
            continue

        # Recherche de mot
        handle_search(word, client, server)



def handle_search_for_graph_simple_sse(word,client,server):
        """Gère la recherche d'un mot"""
        search_token = client.calculate_search_token(word)
        matches = server.search_word(search_token)
        if not matches:
            #log_message("INFO", f"Mot non trouvé")
            return 0
        else:
             #log_message("INFO", f"Mot trouvé dans {len(matches)} fichier(s)")
            temp_files = server.transfer_files_to_client(matches)

            # Déchiffrement et affichage des résultats
            for enc_file in matches:
                server_path = os.path.join(PATHS["server"], enc_file)
                result = client.decrypt_file(enc_file)
                result
            # Nettoyage des fichiers temporaires
            server.cleanup_temp_files(temp_files)


def handle_search(word, client, server):
    """Gère la recherche d'un mot"""
    search_token = client.calculate_search_token(word)
    matches = server.search_word(search_token)
    if not matches:
        log_message("INFO", "Aucun fichier trouvé pour ce mot.")
    else:
        log_message("INFO", f"Mot trouvé dans {len(matches)} fichier(s)")
        temp_files = server.transfer_files_to_client(matches)

        # Déchiffrement et affichage des résultats
        for enc_file in matches:
            server_path = os.path.join(PATHS["server"], enc_file)
            result = client.decrypt_file(enc_file)
            if result:
                log_message("INFO", f"{result}")
            else:
                log_message("ERROR", f"Erreur de déchiffrement pour : {enc_file}")

        # Confirmation de continuation
        while True:
            log_message("INFO", "Souhaitez-vous continuer la recherche ? (y/n) : ")
            confirm = input("> ").strip().lower()
            if confirm in ["y", "yes", "oui"]:
                break
            elif confirm in ["n", "no", "non"]:
                log_message("INFO", "Arrêt par le client.")
                sys.exit(0)
            else:
                log_message("WARNING", "Veuillez entrer 'y' pour continuer ou 'n' pour quitter")

        # Nettoyage des fichiers temporaires
        server.cleanup_temp_files(temp_files)


if __name__ == "__main__":
    main()