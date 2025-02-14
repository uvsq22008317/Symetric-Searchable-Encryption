from src.services.client import Client
from src.services.database import Database
from src.utils.encryptor import encrypt_folder, decrypt_folder, create_index
import os
import src.config

if __name__ == "__main__":
    c1, c2, c3 = Client("Alice"), Client("Bob"), Client("Charlie")
    # TODO : Il faudrait qqchose qui genere des fichiers aleatoires afin de tester

    source, key = ".\src\Clients\Alice", c1.get_key()

    # On encrypte les fichiers dans le dossier d'Alice l'on laisse les fichiers encryptés dans le dossier d'Alice
    encrypt_folder(source=source, key=key)
    # TODO : Il manque l'envoie des fichiers du Serveur au Client

    # TODO : L'index
    create_index(c1)

    # on decrypte les fichiers dans le dossiers d'Alice et on les effaces
    #contenu = decrypt_folder(key=key, source=source)
    #print(contenu)

    # On nettoie les fichiers .enc qui trainent de partout
    src.config.remove_residual_files()