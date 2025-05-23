import base64
from contextlib import asynccontextmanager
import json
import os

from fastapi import FastAPI
from pydantic import BaseModel
from client import Client
from server import Server
from file_generator import FileGenerator
from config import PATHS, log_message




from Crypto.Random import get_random_bytes
from database import Database
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import ast

@asynccontextmanager
async def main(app: FastAPI):

        load_dotenv()
        key =  get_random_bytes(16)
        #writeKey(key)

        database  = Database()

        # Création du client
        client = Client()
        # génération de fichiers aléatoires
        docs  = FileGenerator.generate_random_file(PATHS["client"], num_files=10)

         # Chiffrement des documents revoie les document chiffree
        doc_encrypted , doc_encrypt_info = client.encrypt_folder(docs,key)
        for doc in doc_encrypted:
            database.addFile(doc)

        #write_doc_encrypt_info(doc_encrypt_info)
        # Création de l'index
        index , doc_words_map = client.create_index(docs,key)
    
        #write_doc_words_map(doc_words_map)
    

        write_env(key,doc_words_map,doc_encrypt_info)
        # chiffrement de l'index
        encrypted_index =  client.encrypt_index(index,key)
        database.addIndex(encrypted_index)



       


        # Création du serveur
        server = Server(client)
        yield

        # Interface utilisateur
        log_message("INFO", "Environnement Client/Serveur prêt !")
        log_message("INFO", "Recherche dans index chiffré")
        log_message("INFO", "Donnez le mot que vous cherchez ou quittez avec 'exit'")

app = FastAPI(lifespan=main)     


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Word(BaseModel):
     word: str


@app.get("/generate_documents")
def generate_documents(i :int):
        load_dotenv()
        key =  get_random_bytes(16)
        print(f"KEY IN GENERATE DOC {key}")
        #writeKey(key)

        database  = Database()

        database.deleteAllFiles()

        # Création du client
        client = Client()
        # génération de fichiers aléatoires
        docs  = FileGenerator.generate_random_file(PATHS["client"], num_files=i)

         # Chiffrement des documents revoie les document chiffree
        doc_encrypted , doc_encrypt_info = client.encrypt_folder(docs,key)
        for doc in doc_encrypted:
            database.addFile(doc)

        #write_doc_encrypt_info(doc_encrypt_info)
        # Création de l'index
        index , doc_words_map = client.create_index(docs,key)
    
        #write_doc_words_map(doc_words_map)
        write_env(key,doc_words_map,doc_encrypt_info)
    
        # chiffrement de l'index
        encrypted_index =  client.encrypt_index(index,key)
        database.addIndex(encrypted_index)



       


        # Création du serveur
        server = Server(client)
        yield

        # Interface utilisateur
        log_message("INFO", "Environnement Client/Serveur prêt !")
        log_message("INFO", "Recherche dans index chiffré")
        log_message("INFO", "Donnez le mot que vous cherchez ou quittez avec 'exit'")




@app.post("/search")
def handle_search(wordData: Word):
        
        word = wordData.word
        result = {}
        client = Client()
        database = Database()
        # pour charger le .env mis à jour.
        load_dotenv(override=True)
        key =  base64.b64decode(os.getenv("KEY"))
        print(f"KEY IN SEARCH {key}")
        doc_encrypt_info = ast.literal_eval(os.getenv("DOC_ENCRYPT_INFO"))
        doc_words_map = ast.literal_eval(os.getenv("DOC_WORDS_MAP"))

        """Gère la recherche d'un mot"""
        search_token = client.calculate_search_token(word,doc_words_map,key)
        if (search_token == None ):
              result["result"] = []
              return result
        matches = database.search_word(search_token)
        if not matches:
            log_message("INFO", "Aucun fichier trouvé pour ce mot.")
            result["result"] = []
            return []
        else:
            log_message("INFO", f"Mot trouvé dans {len(matches)} fichier(s)")
            #print(f"search matches : {matches}")
            docsDecrpyted = []
            # Déchiffrement et affichage des résultats
            for enc_doc in matches:
                #log_message("INFO", f" match encrypted found {enc_doc}")
                name_crypted = enc_doc["doc"][0]
                #print(f"name crypted : {name_crypted}")
                doc = database.searchFile(name_crypted)
                #log_message("DOC FOUND hello ", f"{doc}")

                #docsDecrpyted.append(doc)
                if doc:
                   # log_message("INFO", f" doc found {doc}")
                    decrypted_doc = client. decrypt_file(doc,doc_encrypt_info,key)

                    docsDecrpyted.append(decrypted_doc)
                else:
                    log_message("ERROR", f"Erreur de déchiffrement pour : {enc_doc}")

            
            result["result"] = docsDecrpyted
            
            return result


def writeKey(key): 
     if key is None:
        log_message("La clé est numme")
     else:
        write_or_replace( "KEY", base64.b64encode(key).decode("utf-8"))

def write_doc_encrypt_info(en):
      write_or_replace("DOC_ENCRYPT_INFO",en)

def write_doc_words_map(en):
     write_or_replace( "DOC_WORDS_MAP",en)
            

def write_env(key, doc_words_map ,doc_encrypt_info):
      with open(".env", "w") as f:
        encoded_key = base64.b64encode(key).decode("utf-8")

        f.write(f"KEY={encoded_key}\n")
        f.write(f"DOC_ENCRYPT_INFO={doc_encrypt_info}\n")
        f.write(f"DOC_WORDS_MAP={doc_words_map}\n")

def write_or_replace(variable,en):
     exist = False
     with open(".env", "r") as f:
        lines = f.readlines()
        for i, l in enumerate(lines):
             if l.startswith(f"{variable}="):
                  lines[i] =  f"{variable}={en}\n"
                  exist = True
     f.close()
     if (exist):
        with open(".env", "w") as f:
            f.writelines(lines)
        f.close()
     if (not exist):
        with open(".env", "a") as f:
            f.write(f"{variable}={en}\n")                 




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)