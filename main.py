from src.services.client import Client
from src.utils.encryptor import encrypt_folder, decrypt_folder 
from src.utils.index import create_index, encrypt_index
import os
from src.config import remove_residual_files, CLIENTS_PATH, SERVER_PATH
from src.utils.filegen import generate_random_file

if __name__ == "__main__":
    c1 = Client("Alice")
    # TODO : Il faudrait qqchose qui genere des fichiers aleatoires afin de tester

    source, key = c1.get_path(), c1.get_key()

    generate_random_file(".\src\Clients\Charlie")

    encrypt_folder(source=source, key=key)
    # TODO : Il manque l'envoie des fichiers du Serveur au Client

    create_index(source=source)
    encrypt_index(source, key=key)

    remove_residual_files(CLIENTS_PATH)
    remove_residual_files(SERVER_PATH)