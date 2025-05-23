import os
import stat
import shutil
import logging


# Définition du niveau de logs via une variable d’environnement (par defaut INFO)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO") # NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL

# Configuration du logger
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - [%(levelname)s]: %(message)s",
    datefmt="%H:%M:%S"
)

# Fonction utilitaire pour enregistrer un log
def log_message(level, message):
    getattr(logging, level.lower(), logging.info)(message)  # Log en fonction du niveau
    
# Les paths
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
PATHS = {
    "client": os.path.join(BASE_PATH, "Client"),
    "server": os.path.join(BASE_PATH, "Serveur"),
    "utils": os.path.join(BASE_PATH, "utils"),
    "services": os.path.join(BASE_PATH, "services"),
    "backup": os.path.join(BASE_PATH, "Backup")
}

# Valeurs globales
EXTENTIONS = (".txt", ".md")
ENCODED_EXTENTION = ".enc"

# Noms généré lors de la génération de fichiers
FILENAMES_LIST = [
    "file", "document", "log", 
    "report", "resume", "notes", 
    "journal", "data", "backup"
    ]

FRUITS_LIST = [
    "Banane", "Pomme", "Fraise", "Mangue", "Orange",
    "Raisin", "Pastèque", "Ananas", "Cerise", "Pêche",
    "Poire", "Framboise", "Melon", "Kiwi", "Grenade",
    "Papaye", "Fruit_du_dragon", "Litchi", "Noix_de_coco", "Myrtille",
    "Abricot", "Figue", "Kaki", "Goyave", "Citron"
]

def remove_residual_files(path):
    if not os.path.exists(path):
        return
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
        if os.path.isdir(file_path):
            remove_residual_files(file_path)
    for dossier in os.listdir(path):
        file_path = os.path.join(path, dossier)
        shutil.rmtree(file_path)

