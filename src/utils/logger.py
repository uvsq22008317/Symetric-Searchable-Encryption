import logging
import os

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
