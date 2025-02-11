from src.SSE_client import Client
from src.SSE import Encryptor
from src.SSE_bdd import Database
import os

if __name__ == "__main__":
    c1, c2, c3 = Client("Alice"), Client("Bob"), Client("Charlie")

    #/!\ Ne pas oublier de supprimer les ".enc" dans les dossiers Client a chaque fois que l'on relance le programme
    # Cela permet de relancer le programme directement sans avoir de fichier .enc
    for document in os.listdir(c1.get_path()):
        if document.endswith(".enc"):
            os.remove(c1.get_path() + document)

    # print(c1)
    e = Encryptor()

    # Creation de l'index basé sur les documents d'Alice
    e.create_index(c1)
    # Avec la clé d'Alice, on chiffre ses documents que l'on place son propre dossier.
    e.encrypt_documents(c1.get_key(), c1.get_path(), c1.get_path())


    contenu = e.decrypt_documents(c1.get_key(), c1.get_path())
    print(contenu)

