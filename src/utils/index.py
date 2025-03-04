import os
import json
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util import Counter
from src.utils.encryptor import pad_bit


import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

def create_index(source):
    # TODO : Erreur si la source n'est pas un dossier valide
    # On crée l'index
    config.log_message("INFO", f"Création de l'index en cours.")
    index = {}
    for document in os.listdir(source):
        doc_path = os.path.join(source, document)
        
        # Vérification de l'existance du fichier
        if document.endswith(config.EXTENTIONS) and os.path.isfile(doc_path):
            config.log_message("DEBUG", f"Lecture du fichier {document}")

            # Parcours du fichier en considerant chaque mot
            with open(doc_path, "r", encoding="utf-8") as file:  
                for line in file:                                        
                    for word in line.split():                                      
                        clean_word = word.strip(",.?!:;()[]{}\"'\n\t-")
                        if clean_word not in index:
                            index[clean_word] = []
                        if document not in index[clean_word]: 
                            index[clean_word].append(document)

        index_path = os.path.join(source, "index.json")
        try:
            with open(index_path, "w", encoding="utf-8") as json_file:
                json.dump(index, json_file, indent=4, ensure_ascii=True)
        except Exception as e:
            config.log_message("ERROR", f"Erreur lors de la création de l'index : {e}")
            return   
    config.log_message("INFO", f"Index a créé avec succès.")

def encrypt_index(source, key):
    config.log_message("DEBUG", f"Encryption de l'Index de en cours.")    
    try:
        with open(os.path.join(source, "index.json"), 'r', encoding='utf-8') as index_file:
            index = json.load(index_file)
    except Exception as e:
        config.log_message("ERROR", f"Erreur lors de l'ouverture de l'index lors de l'encryption : {e}")
        return
    cipher = AES.new(key, AES.MODE_ECB)
    encrypted_index = {}
    config.log_message("WARNING", f"Mode ECB lors de l'encryption de l'index !")
    for word, docs in index.items():
        # Encryption en CBC
        encrypted_word = cipher.encrypt(pad_bit(word.encode("utf-8"))).hex()
        encrypted_docs = [cipher.encrypt(pad_bit(doc.encode("utf-8"))).hex() for doc in docs]
        encrypted_index[encrypted_word] = encrypted_docs
        try:
            encrypted_index_path = os.path.join(source, 'encrypted_index.json')
            with open(encrypted_index_path, "w", encoding="utf-8") as encrypted_json_file:
                json.dump(encrypted_index, encrypted_json_file, indent=4, ensure_ascii=True)
        except Exception as e:
            config.log_message("ERROR", f"Erreur lors de la création de l'index encrypté : {e}")
            return   
    config.log_message("INFO", f"Index a créé encrypté avec succès.")
