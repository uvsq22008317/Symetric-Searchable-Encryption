from Client import Client
from Crypto.Random import get_random_bytes
from Serveur import Serveur
import os
from Crypto.Cipher import AES
#import random

# On va simuler le comportement d'Alice

# Liste de mots aléatoires
# word_list =["chat","chien","soleil","lune","ordinateur","école","maison","forêt","rivière","montagne","voiture","avion","musique","plage","neige","sport","livre", "table","fenêtre","jardin","arbre", "océan", "horizon","étoile","pont", "chemin","parfum","voyage","drapeau", "histoire","vent","ciel","mer", "cascade","bâteau","aventure","galaxie","train","sourire", "clavier","château","danse","éclair","lampe","boussole","science","colline","fleur","rêve","ombre"]

# On genere aleatoirement une clé sans cadancement de clé
key = get_random_bytes(16)

# Client = l'instance Alice et encryptor = ordinateur
Alice = Client(key)

# Alice crée son index en clair assez facilement dans un json
Alice.create_index()

# Générer 10 fichiers
# for i in range(1, 11):
#    file_name = f"text_{i}.txt"
#    file_path = os.path.join("./Client/", file_name)
#    random_words = random.choices(word_list, k=25)

    # Écrire les mots dans le fichier
#    with open(file_path, "w", encoding="utf-8") as file:
#        file.write(" ".join(random_words))

# Alice chiffre ses documents et les envoie
Alice.encrypt_documents()

# Alice efface ses propres documents, ici nous n'allons pas le faire
#Alice.delete_documents()

# La database de "Bob"
BDD = Serveur(encryptor=Alice)

# Bob recoit l'index chiffré d'Alice
Alice.send_index()

# Alice cherche le mot "question"
buffer = "musique"
files = BDD.search(buffer)
print("Alice cherche le mot :", buffer)
print("Alice a reçu :", files)

# Alice decrypte les documents à l'aide de sa clé
if files:
  for file in files:
    encrypted_path = os.path.join(Alice.client_path, file)
    with open(encrypted_path, 'rb') as f:
      encrypted_data = f.read()
      iv = encrypted_data[:16]
      encrypted_content = encrypted_data[16:]
      cipher = AES.new(key, AES.MODE_CBC, iv)
      decrypted_content = cipher.decrypt(encrypted_content)
      try:
        decoded = decrypted_content.decode('utf-8')
        print("\nFichier :", file)
        print(decoded)
      except UnicodeDecodeError:
        print("Erreur dans le décodage pour du fichier.")

