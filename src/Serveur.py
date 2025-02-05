import os
import json
from Crypto.Cipher import AES

class Client:
  def __init__(self, key):
    self.key = key
    client_path = "./Client/"
    self.client_path = client_path
    if not os.path.exists(client_path):      # 1. Si le fichier Client n'existe pas, on le crée avec un fichier temporaire
      os.makedirs(client_path)
      try:
        with open('Client/tmp.txt', 'w') as f:
          f.write("The question isn\'t, who am I." 
                  + " The question is where am I?")
      except FileNotFoundError:
        print("Le fichier temporaire n'a pas pu être crée... " 
        + "Il se peut que le dossier Client ne puisse pas être crée...")
    else:
      print("Dossier Client déjà crée...")
    self.files = []
    extentions = (".txt")                   # /!\ On accepte que ".txt" pour l'instant
    for file in os.listdir(client_path):
      if file.endswith(extentions):
        self.files.append(file)

  def pad(self, data):
    padding_length = 16-(len(data)%16)                       # Creation des blocs de 16 octets pour AES
    return data + b'8' + ('0'*(padding_length-1)).encode()   # Print : b'<data>800000'

  def unpad(self,data):
    return data[:-data[-1]]
    # on recupere la valeur correspondant au nombre d'octets ajouté et on enleve ce nombre de charactere
  
  def decrypt_document(self, encrypted_data):
    with open(self.client_path + encrypted_data, 'rb') as f:
      iv = f.read(16)
      encrypted_content = f.read()
      cipher = AES.new(self.key, AES.MODE_CBC, iv)
      decrypted_content = self.unpad(cipher.decrypt(encrypted_content))
    return decrypted_content.decode()

  def encrypt_word(self, word):
    cipher = AES.new(self.key, AES.MODE_ECB)   # On veut chiffrer le mot en mode ECB
    padded_word = self.pad(word.encode())      # On le pad avant pour que l'on obtienne des blocs de 16 octets
    return cipher.encrypt(padded_word)         # On retourne Enc(k, w) sous format 'bytes'

  def create_index(self, output_json="Client/index.json"):
    index = {}
    for file_path in self.files:
      if not os.path.exists(self.client_path + file_path):
        print("Erreur : Un fichier est écrit et pourtant il n'existe pas ?...")
        break                                                                         # Gestion des cas d'erreur
      with open(self.client_path + file_path, 'r', encoding='utf-8') as file:         # Creation de l'index
        for line in file:                                                             # Exemple ci dessous ligne par ligne :
          for word in line.split():                                                   # ['The', 'question', 'isn', 't,', ...]
            clean_word = self.encrypt_word(word.strip(",.?!:;()[]{}\"'\n\t-")).hex()  # [Enc(k, 'The'), Enc(k, 't'), ...]
            if clean_word not in index:                                               # Si le mot n'est pas dans l'index
              index[clean_word] = []                                                  # On crée le mot dans l'index
            if os.path.splitext(file_path)[0] + '.enc' not in index[clean_word]:      # Si tmp.enc n'est pas dans Enc(k, 'The') 
              index[clean_word].append(os.path.splitext(file_path)[0] + '.enc')       # Alors => {Enc(k, 'The'): ['tmp.txt']}
                
      # Sauvegarde du dictionnaire en JSON
      with open(output_json, 'w', encoding='utf-8') as json_file:
        json.dump(index, json_file, ensure_ascii=True)

  # Encryption d'un document nommé doc_name
  #
  #
  def encrypt_document(self, doc_name, server_path="./Serveur/"):
    cipher = AES.new(self.key, AES.MODE_CBC)                                          # On chiffre le doc en AES mode CBC
    iv = cipher.iv
    with open(self.client_path + doc_name, 'r', encoding='utf-8') as file:
      encrypted_content = cipher.encrypt(self.pad(file.read().encode()))
      encrypted_doc = server_path + os.path.splitext(doc_name)[0] + '.enc'
      with open(encrypted_doc, 'wb') as f:                                            # 'wb' : Write binary pour .enc
        f.write(bytes(iv) + encrypted_content)                                        # Ecrit dans le fichier .enc
        
  # Encryption des documents '.txt' donnée par le Client
  def encrypt_documents(self, server_path="./Serveur/"):
    for document in self.files:
      self.encrypt_document(document, server_path)

  # Envoie au serveur l'index
  def send_index(self, server_path="./Serveur/"):
    with open(self.client_path + "index.json", "r", encoding="utf-8") as index_client:
      new_index = json.load(index_client)
      # Écrire le JSON dans un nouveau fichier
      with open(server_path + "index.json", "w", encoding="utf-8") as index_server:
          json.dump(new_index, index_server, indent=4, ensure_ascii=True)
    os.remove(self.client_path + "index.json")

  def delete_documents(self):
    pass # Not implemented
