import os
import stat
from utils.logger import log_message

# Les paths
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
CLIENTS_PATH = os.path.join(BASE_PATH, "Clients")
SERVER_PATH = os.path.join(BASE_PATH, "Serveur")
UTILS_PATH = os.path.join(BASE_PATH, "utils")
SERVICES_PATH = os.path.join(BASE_PATH, "services")

# Valeurs globales
EXTENTIONS = (".txt", ".md")
ENCODED_EXTENTION = ".enc"


"""
    Initialise les dossiers Clients et Serveur en les vidant de tout contenu
"""
def setup():
    log_message("INFO", "Initialisation des dossiers Clients et Serveur")

    # Creation du dossier Clients
    if not os.path.exists(CLIENTS_PATH):
        os.makedirs(CLIENTS_PATH)
        log_message("INFO", f"Création du dossier Clients : {CLIENTS_PATH}")
    # Destruction et Re-creation du dossier Clients
    else:
        log_message("INFO", f"Nettoyage du dossier Clients : {CLIENTS_PATH}")
        for file in os.listdir(CLIENTS_PATH):
            file_path = os.path.join(CLIENTS_PATH, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
            if os.path.isdir(file_path):
                os.system('rmdir /S /Q "{}"'.format(file_path))


    # Création du dossier Serveur
    if not os.path.exists(SERVER_PATH):
        os.makedirs(SERVER_PATH)
        log_message("INFO", f"Création du dossier Serveur : {SERVER_PATH}")
    # Destruction et Re-creation du dossier Clients
    else:
        log_message("INFO", f"Nettoyage du dossier Serveur : {SERVER_PATH}")
        for file in os.listdir(SERVER_PATH):
            file_path = os.path.join(SERVER_PATH, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
            if os.path.isdir(file_path):
                os.system('rmdir /S /Q "{}"'.format(file_path))

def remove_residual_files(path=BASE_PATH):
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if os.path.isfile(file_path) and file.endswith(ENCODED_EXTENTION):
            os.remove(file_path)
        if os.path.isdir(file_path):
            remove_residual_files(file_path)