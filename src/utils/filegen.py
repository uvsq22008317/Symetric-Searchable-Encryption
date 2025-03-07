import os
import random
import string
import config
from utils.logger import log_message

def generate_random_file(source, num_files=5):
    try:
        os.makedirs(source, exist_ok=True)
    except Exception as e:
        log_message("ERREUR", f"Erreur lors de la création du répertoire: {e}")
        return
    if num_files <= 0:
        log_message("ERREUR", "Le nombre de fichiers doit être supérieur à zéro")
        return
    for i in range(num_files):
        name = random.choice(config.FILENAMES_LIST) + f"_{i+1}" + random.choice(config.EXTENTIONS)
        file = os.path.join(source, name)
        with open(file, "w", encoding="utf-8") as f:
            text = ' '.join(
                random.choices(config.FRUITS_LIST, k=random.randint(7, 15)))
            f.write(text)
    log_message("INFO", f"{num_files} fichiers générés dans {source}")