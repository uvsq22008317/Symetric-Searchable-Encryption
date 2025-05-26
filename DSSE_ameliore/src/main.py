import json
import os
import shutil
from DSSE_ameliore.src.client import Client
from DSSE_ameliore.src.server import Server
from DSSE_ameliore.src.file_generator import FileGenerator
from DSSE_ameliore.src.config import EXTENTIONS, PATHS, log_message, remove_residual_files, FRUITS_LIST
import sys
import time


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

        elif word.lower() == "update":
            # Gestion de la mise à jour de document
            handle_update_document(client)
            server.reload_index()
            continue

        elif word.lower() in ["add", "ajouter"]:
            handle_add_files(client)
            server.reload_index()
            continue

        elif word.lower() in ["remove", "delete", "supprimer"]:
            handle_remove_file(client)
            continue

        if not word:
            continue

        # Recherche de mot
        handle_search(word, client, server)




def handle_search_for_graph_dsse_ameliore(word,client,server):
        """Gère la recherche d'un mot"""
        search_token = client.calculate_search_token(word)
        matches = server.search_word(search_token)
        if not matches:
            log_message("INFO", f"Mot non trouvé")
            return 0
        else:
            log_message("INFO", f"Mot trouvé dans {len(matches)} fichier(s)")
            temp_files = server.transfer_files_to_client(matches)

            # Déchiffrement et affichage des résultats
            for enc_file in matches:
                result = client.decrypt_file(enc_file)
                result
            # Nettoyage des fichiers temporaires
            server.cleanup_temp_files(temp_files)



def handle_update_document(client):
    """Gère la mise à jour d'un document"""
    log_message("INFO", "Mise à jour d'un document")

    if not client.doc_name_map:
        log_message("INFO", "Aucun document disponible pour mise à jour")
        return
    log_message("INFO", "Sélectionnez le document à mettre à jour :")
    docs = sorted(client.doc_name_map.keys())
    for i, doc in enumerate(docs, 1):
        log_message("INFO", f"{i}: {doc}")

    try:
        choice = int(input("> ")) - 1
        if choice < 0 or choice >= len(docs):
            log_message("ERROR", "Choix invalide")
            return
        
        doc_name = docs[choice]
        if client.update_document(doc_name):
            log_message("INFO", "Document mis à jour avec succès")
        else:
            log_message("ERROR", "Échec de la mise à jour")

    except (ValueError, IndexError):
        log_message("ERROR", "Choix invalide")

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


def handle_add_files(client):
    log_message("INFO", "Fichiers disponibles dans le client:")
    
    client_files = []

    for element in os.listdir(PATHS["client"]):
        full_path = os.path.join(PATHS["client"], element)
        
        if element.endswith(EXTENTIONS) and os.path.isfile(full_path):
            client_files.append(element)

    if not client_files:
        log_message("INFO", "Aucun fichier disponible dans le client")
        return
    
    for i, f in enumerate(client_files, 1):
        log_message("INFO", f"{i}. {f}")
    
    log_message("INFO", "Entrez le numéro du fichier à ajouter:")
    
    while True:
        choice = input("> ").strip()
        if choice.lower() in ['q', 'quit', 'exit']:
            return
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(client_files):
                filename = client_files[idx]
                ok = client.add_file(filename)
                if ok:
                    log_message("INFO", "Ajout réussi!")
                else:
                    log_message("ERROR", "Échec de l'ajout")
                break
            else:
                log_message("WARNING", "Numéro invalide")
        except ValueError:
            log_message("WARNING", "Veuillez entrer un numéro valide")


def handle_remove_file(client):
    backup_files = []

    for element in os.listdir(PATHS["backup"]):
        full_path = os.path.join(PATHS["backup"], element)
        
        if element.endswith(EXTENTIONS) and os.path.isfile(full_path):
            backup_files.append(element)

    if not backup_files:
        log_message("INFO", "Aucun fichier disponible dans le backup")
        return
    
    for i, f in enumerate(backup_files, 1):
        log_message("INFO", f"{i}. {f}")
    
    while True:
        log_message("INFO", "Entrez le numéro du document à supprimer ou quittez avec 'exit':")
        choice = input("> ").strip()
        if choice.lower() in ['q', 'quit', 'exit']:
            return
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(client.doc_name_map):
                filename = list(client.doc_name_map.keys())[idx]
                client.remove_document(filename)
            else:
                log_message("WARNING", "Numéro invalide")
        except ValueError:
            log_message("WARNING", "Veuillez entrer un numéro valide")

if __name__ == "__main__":
    main()