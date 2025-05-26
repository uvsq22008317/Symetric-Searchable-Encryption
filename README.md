# SSE : Symetric Searchable Encryption

# Structure

├── DSSE
├── DSSE_ameliore
├── generationGraphes
├── siteDSSEAm
└── SSE

Chaque dossier correspond à une implementation de SSE décrit dans le rapport ainsi que le code pour pouvoir faire les graphes donnés dans le rapport.

Pour chacun des dossiers on a les fichiers suivants : 

utils : Contient les fichiers utilitaires
- encryptor.py : Les fonctions de chiffrement/dechiffrement
- logger.py : Permet d'avoir des "loggers" affichant l'état du code
- index.py : Les fonctions en rapport avec la création de l'index
services : Les actions des clients et du serveur
- client.py / database.py : respectivement les actions de chacun 

# Utilisation
```bash
# Dans le dossier source  : Symetric-Searchable-Encryption 
# Pour lancer le DSSE_ameliore
python3 -m DSSE_ameliore.src.main
# Pour lancer le SSE
python3 -m SSE.main 
# Pour lancer le DSSE
python3 -m DSSE.src.main
```


# Sources
Logging : https://realpython.com/python-logging/
Comment supprimer un dossier : [Shutil : https://stackoverflow.com/questions/303200/how-do-i-remove-delete-a-folder-that-is-not-empty](https://stackoverflow.com/questions/2656322/shutil-rmtree-fails-on-windows-with-access-is-denied)

# Dépendance(s)
```bash
pip install pycryptodome
```

