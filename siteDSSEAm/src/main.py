from contextlib import asynccontextmanager
import json
import os
import shutil

from fastapi import FastAPI
from pydantic import BaseModel
from client import Client
from server import Server
from file_generator import FileGenerator
from config import PATHS, log_message, remove_residual_files

import sys



from Crypto.Random import get_random_bytes
from database import Database

from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def main(app: FastAPI):

        key =  get_random_bytes(16)
        app.state.key = key
        print(f"=================KEY :{app.state.key}")

        database  = Database()

        # Création du client
        client = Client()
        # génération de fichiers aléatoires
        docs  = FileGenerator.generate_random_file(PATHS["client"], num_files=10)

         # Chiffrement des documents revoie les document chiffree
        doc_encrypted , doc_encryp_info = client.encrypt_folder(docs,key)
        for doc in doc_encrypted:
            database.addFile(doc)

        app.state.doc_encryp_info  = doc_encryp_info

        # Création de l'index
        index , doc_words_map = client.create_index(docs,key)
    
        app.state.doc_words_map = doc_words_map
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
        

def handle_update_document(client):
        """Gère la mise à jour d'un document"""
        log_message("INFO", "Mise à jour d'un document")
        index_path = os.path.join(PATHS["client"], "index.json")
        
        if not os.path.exists(index_path):
            log_message("ERROR", "Index non trouvé dans le dossier client")
            return
            
        with open(index_path, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        # Récupération de tous les documents
        all_docs = set()
        for docs in index.values():
            all_docs.update(docs)
        
        if not all_docs:
            log_message("INFO", "Aucun document disponible pour mise à jour")
            return
        
        log_message("INFO", "Sélectionnez le document à mettre à jour :")
        for i, doc in enumerate(sorted(all_docs)):
            log_message("INFO", f"{i + 1}: {doc}")

        try:
            choice = int(input("> ")) - 1
            if choice < 0 or choice >= len(all_docs):
                log_message("ERROR", "Choix invalide")
                return
            doc_name = sorted(all_docs)[choice]
            log_message("INFO", f"Entrez le nouveau contenu pour {doc_name}:")
            new_content = input("> ").strip()

            if client.update_document(doc_name, new_content):
                log_message("INFO", "Document mis à jour avec succès")
            else:
                log_message("ERROR", "Échec de la mise à jour")
                
        except (ValueError, IndexError):
            log_message("ERROR", "Choix invalide")



@app.post("/search")
def handle_search(wordData: Word):
        word = wordData.word
        result = {}
        client = Client()
        database = Database()

        """Gère la recherche d'un mot"""
        print(f"=================KEY :{app.state.key}")
        search_token = client.calculate_search_token(word,app.state.doc_words_map,app.state.key)
        if (search_token == None ):
              result["result"] = []
              return result
        print(f"search token found : {search_token}")
        matches = database.search_word(search_token)
        if not matches:
            log_message("INFO", "Aucun fichier trouvé pour ce mot.")
        else:
            log_message("INFO", f"Mot trouvé dans {len(matches)} fichier(s)")
            print(f"search matches : {matches}")
            docsDecrpyted = []
            # Déchiffrement et affichage des résultats
            for enc_doc in matches:
                log_message("INFO", f" match encrypted found {enc_doc}")
                name_crypted = enc_doc["doc"][0]
                print(f"name crypted : {name_crypted}")
                doc = database.searchFile(name_crypted)
                log_message("DOC FOUND hello ", f"{doc}")

                #docsDecrpyted.append(doc)
                if doc:
                    log_message("INFO", f" doc found {doc}")
                    decrypted_doc = client. decrypt_file(doc,app.state.doc_encryp_info,app.state.key)

                    docsDecrpyted.append(decrypted_doc)
                else:
                    log_message("ERROR", f"Erreur de déchiffrement pour : {enc_doc}")

            
            result["result"] = docsDecrpyted
            
            return result

@app.get("/key")
def getKey(): 
        return get_random_bytes(16)
#if __name__ == "__main__":
#    main()

#if __name__ == "__main__":
#    import uvicorn

#    uvicorn.run(app, host="127.0.0.1", port=8000)