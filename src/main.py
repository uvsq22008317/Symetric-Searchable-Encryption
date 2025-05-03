import os
from Crypto.Random import get_random_bytes
from utils.encryptor import encrypt_folder, decrypt_file, search_word
from config import PATHS, ENCODED_EXTENTION, EXTENTIONS, log_message, remove_residual_files
from utils.filegen import generate_random_file
from utils.index import create_index, encrypt_index, add_file_from_backup, remove_document
import sys
import shutil
import hmac
import hashlib

def add_files(key, doc_name_map):
    log_message("INFO", "Fichiers disponibles dans le backup:")
    
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
    
    log_message("INFO", "Entrez le numéro du fichier à ajouter:")
    
    while True:
        choice = input("> ").strip()
        if choice.lower() in ['q', 'quit', 'exit']:
            return
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(backup_files):
                filename = backup_files[idx]
                ok = add_file_from_backup(key, filename, doc_name_map)
                if ok:
                    log_message("INFO", "Ajout réussi!")
                else:
                    log_message("ERROR", "Échec de l'ajout")
                break
            else:
                log_message("WARNING", "Numéro invalide")
        except ValueError:
            log_message("WARNING", "Veuillez entrer un numéro valide")


def remove_file(doc_name_map, key):
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
    
    log_message("INFO", "Entrez le numéro du document à supprimer:")
    
    while True:
        choice = input("> ").strip()
        if choice.lower() in ['q', 'quit', 'exit']:
            return
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(doc_name_map):
                filename = list(doc_name_map.keys())[idx]
                remove_document(key, filename, doc_name_map)
            else:
                log_message("WARNING", "Numéro invalide")
        except ValueError:
            log_message("WARNING", "Veuillez entrer un numéro valide")


if __name__ == "__main__":
    if not os.path.exists(PATHS["client"]):
        os.makedirs(PATHS["client"])
    if not os.path.exists(PATHS["server"]):
        os.makedirs(PATHS["server"])
    if not os.path.exists(PATHS["backup"]):
        os.makedirs(PATHS["backup"])

    # Suppression des fichiers résiduels pour avoir un environnement propre
    remove_residual_files(PATHS["client"])
    remove_residual_files(PATHS["server"])
    remove_residual_files(PATHS["backup"])

    # Création un fichiers texte temporaires
    generate_random_file(PATHS["client"], num_files=10)

    # On crée son index en clair
    create_index(PATHS["client"])

    # La clé du client est généré
    key = get_random_bytes(16)

    # Chiffrement le dossier Client
    clair_chiffree_doc = encrypt_folder(key, PATHS["client"])

    # Récupération les fichiers chiffrés
    encrypted_files = [
        f for f in os.listdir(PATHS["client"])
        if f.endswith(ENCODED_EXTENTION)
    ]

    # Si on génére aucun fichier dans Client logiquement il y a une erreur
    if not encrypted_files:
        log_message("ERROR", "Aucun fichier encrypté trouvé")
        sys.exit(1)

    # Déplacement des fichiers chiffrés vers le serveur
    for enc_file in encrypted_files:
        src_path = os.path.join(PATHS["client"], enc_file)
        dst_path = os.path.join(PATHS["server"], enc_file)

        for original_name, encrypted_name in clair_chiffree_doc.items():
            if encrypted_name == enc_file:
                original_path = os.path.join(PATHS["client"], original_name)
                backup_path = os.path.join(PATHS["backup"], original_name)

                # Sauvegarde du fichier en clair dans le backup
                if os.path.exists(original_path):
                    shutil.copy2(original_path, backup_path)
                    log_message("DEBUG", f"Copie du fichier clair dans le backup : {original_name}")
                break
        # Sauvegarde du fichier chiffrée dans le serveur
        shutil.move(src_path, dst_path)
        log_message("DEBUG", f"Fichier déplacé vers le serveur : {enc_file}")

    # On chiffre l'index
    encrypted_index = encrypt_index(PATHS["client"], key, clair_chiffree_doc)
    
    # On deplace l'index chiffré du client vers le serveur, s'il n'existe pas on affiche une erreur
    try :
        src_path_index = os.path.join(PATHS["client"], "encrypted_index.json")
        dst_path_index = os.path.join(PATHS["server"], "encrypted_index.json")
        shutil.move(src_path_index, dst_path_index)
    except Exception as e:
        log_message("ERROR", f"Erreur lors du déplacement de l'index : {e}")
        sys.exit(1)

    # Nettoyage du dossier client
    log_message("INFO", "Nettoyage du dossier client en cours...")
    for file in os.listdir(PATHS["client"]):
        full_path = os.path.join(PATHS["client"], file)
        if os.path.isfile(full_path) and file not in ("index.json", "encrypted_index.json"):
            try:
                os.remove(full_path)
                log_message("DEBUG", f"Fichier supprimé : {file}")
            except Exception as e:
                log_message("ERROR", f"Impossible de supprimer {file} : {e}")

    log_message("INFO", "Environnement Client/Serveur pret !")
    log_message("INFO", "Recherche dans index chiffré")
    log_message("INFO", "Commandes disponibles:")
    log_message("INFO", "- Tapez un mot pour rechercher")
    log_message("INFO", "- 'add' pour ajouter un document/fichier du backup")
    log_message("INFO", "- 'remove' pour supprimer un document/fichier du backup")
    log_message("INFO", "- 'exit' pour quitter")

    while True:
        user_input = input("> ").strip()
        if user_input.lower() in ["exit", "quit", "break", "q", "stop", "quitter"]:
            log_message("INFO", "Le Client a quitté la connexion")
            break
        
        elif user_input.lower() in ["add", "ajouter"]:
            add_files(key, clair_chiffree_doc)
            continue

        elif user_input.lower() in ["remove", "delete", "supprimer"]:
            remove_file(clair_chiffree_doc, key)
            continue

        else:
            word = user_input
            if not word:
                continue

            matches = search_word(word, key)
            if not matches:
                log_message("INFO", "Aucun fichier trouvé pour ce mot.")
            else:
                log_message("INFO", f"Mot trouvé dans {len(matches)} fichier(s)")
                temp_files = []

                for enc_file in matches:
                    server_path = os.path.join(PATHS["server"], enc_file)
                    client_path = os.path.join(PATHS["client"], enc_file)

                    if os.path.exists(server_path):
                        # Copier vers le Client
                        shutil.copy2(server_path, client_path)
                        temp_files.append(client_path)
                        log_message("DEBUG", f"Fichier transféré temporairement : {enc_file}")

                        # Déchiffrement du fichier
                        result = decrypt_file(key, server_path)
                        if result:
                            log_message("INFO", f"{result}")
                        else:
                            log_message("ERROR", f"Erreur de déchiffrement pour : {enc_file}")
                    else:
                        log_message("WARNING", f"Fichier non trouvé sur le serveur : {server_path}")

                # Validation du Client (sert pour debug)
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

                # On efface l'environnement du Client
                for file in temp_files:
                    try:
                        os.remove(file)
                        log_message("DEBUG", f"Fichier temporaire supprimé : {os.path.basename(file)}")
                    except Exception as e:
                        log_message("ERROR", f"Erreur de suppression du fichier {file} : {e}")
