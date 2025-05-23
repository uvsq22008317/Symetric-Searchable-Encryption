import os
import random
from config import log_message, FILENAMES_LIST, EXTENTIONS, FRUITS_LIST


class FileGenerator:
    @staticmethod
    def generate_random_file(source, num_files=10000):
        log_message("INFO",f"nombre de documents : {num_files}")
        if num_files <= 0:
            log_message("ERREUR", "Le nombre de fichiers doit être supérieur à zéro")
            return
        list_document=[]
        for i in range(num_files):
            name = random.choice(FILENAMES_LIST) + f"_{i+1}" + random.choice(EXTENTIONS)
            text = ' '.join(
                    random.choices(FRUITS_LIST, k=random.randint(7, 1000)))
            document = { "name": name, "text": text}
            list_document.append(document)
        return list_document