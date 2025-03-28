# Structure
| nonce (8) | iv (16) | name_len (4) | encrypted_name | encrypted_content |

utils : Contient les fichiers utilitaires
- encryptor.py : Les fonctions de chiffrement/dechiffrement
- logger.py : Permet d'avoir des "loggers" affichant l'état du code
- index.py : Les fonctions en rapport avec la création de l'index
services : Les actions des clients et du serveur
- client.py / database.py : respectivement les actions de chacun 

# Sources
Logging : https://realpython.com/python-logging/
Comment supprimer un dossier : [Shutil : https://stackoverflow.com/questions/303200/how-do-i-remove-delete-a-folder-that-is-not-empty](https://stackoverflow.com/questions/2656322/shutil-rmtree-fails-on-windows-with-access-is-denied)

# Dépendance(s)
```bash
pip install pycryptodome
```

# Utilisation
```bash
# Dans le dossier source faire
python -m main.py
```