import json
import os
import shutil
from client import Client
from server import Server
from file_generator import FileGenerator
from config import PATHS, log_message, remove_residual_files
import sys

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
            continue

        if not word:
            continue

        # Recherche de mot
        handle_search(word, client, server)

def handle_update_document(client):
    """Gère la mise à jour d'un document"""
    log_message("INFO", "Mise à jour d'un document")
    index_path = os.path.join(PATHS["client"], "index.json")
    
    if not os.path.exists(index_path):
        log_message("ERROR", "Index non trouvé dans le dossier client")
        return
        
    with open(index_path, 'r', encoding='utf-8') as f:
        index = json.load(f)
    
    # Récupération de tous les documents
    all_docs = set()
    for docs in index.values():
        all_docs.update(docs)
    
    if not all_docs:
        log_message("INFO", "Aucun document disponible pour mise à jour")
        return
    
    log_message("INFO", "Sélectionnez le document à mettre à jour :")
    for i, doc in enumerate(sorted(all_docs)):
        log_message("INFO", f"{i + 1}: {doc}")

    try:
        choice = int(input("> ")) - 1
        if choice < 0 or choice >= len(all_docs):
            log_message("ERROR", "Choix invalide")
            return
        doc_name = sorted(all_docs)[choice]
        log_message("INFO", f"Entrez le nouveau contenu pour {doc_name}:")
        new_content = input("> ").strip()

        if client.update_document(doc_name, new_content):
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
            result = client.decrypt_file(server_path)
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