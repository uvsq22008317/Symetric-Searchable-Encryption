import os
from Crypto.Random import get_random_bytes
from utils.encryptor import encrypt_folder, decrypt_file, search_word
from config import PATHS, ENCODED_EXTENTION, log_message, remove_residual_files
from utils.filegen import generate_random_file
from utils.index import create_index, encrypt_index
import sys
import shutil
import hmac
import hashlib

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
    log_message("INFO", "Donnez le mot que vous chercher ou quitter avec \'exit\'")

    while True:
        word = input("> ").strip()
        if word.lower() in ["exit", "quit", "break", "q", "stop", "quitter"]:
            log_message("INFO", "Le Client a quitté la connexion")
            break

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
