from src.services.client import Client
from src.utils.encryptor import encrypt_folder, decrypt_folder 
from src.utils.index import create_index, encrypt_index
import os
from src.config import remove_residual_files, CLIENTS_PATH, SERVER_PATH
from src.utils.filegen import generate_random_file
from argparse import ArgumentParser, SUPPRESS
import sys

def do_command():
    while True:
        try:
            parser = ArgumentParser(
                prog='Searchable Symmetric Encryption',
                description='Simulation d\'un SSE basé sur differentes implémentations',
                add_help=False
            )
            subparsers = parser.add_subparsers(dest='commande', required=True)
            # Commande quit
            subparsers.add_parser('quit', help='Quitte le programme')
            # Commande create-client
            parser_client = subparsers.add_parser('create-client', help='Créer un client')
            parser_client.add_argument('name', help='Nom du client')
            # Commande create-server
            parser_server = subparsers.add_parser('create-server', help='Créer un serveur')
            # Commande change-log
            parser_logs = subparsers.add_parser('change-logs', help='Définition du niveau de logs via une variable d\'environnement (par defaut INFO)')
            parser_logs.add_argument('level', help='Le niveau du logger')

            parser.add_argument('-v', '--version', action='version', version='1.0')
            parser.add_argument('-h', '--help', action='help', default=SUPPRESS, help='affiche l\'aide')

            user_input = input("Entrez votre action.\n>")
            args = parser.parse_args(user_input.split())              
            return args
        except SystemExit:
            continue


if __name__ == "__main__":
    while True:
        args = do_command()
        match args.commande:
            case "quit":
                remove_residual_files(CLIENTS_PATH)
                remove_residual_files(SERVER_PATH)
                sys.exit(0)
            case "create-client":
                try:
                    Client(args.name)
                    print(f"create client : {args.name}...")
                except NameError as e:
                    print(e)
                    continue
            case "create-server":
                print("create-server...")
            case "change-logs":
                if args.level in ["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                    print("Change logger ! ")
                    os.environ["LOG_LEVEL"] = args.level
                else:
                    print(f"Invalid log level: {args.level}")
                    continue
            case _:
                print("err ?")

    #c1 = Client("Alice")
    # TODO : Il faudrait qqchose qui genere des fichiers aleatoires afin de tester

    #source, key = c1.get_path(), c1.get_key()

    #generate_random_file(source = source)

    #encrypt_folder(source=source, key=key)
    # TODO : Il manque l'envoie des fichiers du Serveur au Client

    #create_index(source=source)
    #encrypt_index(source, key=key)

    #remove_residual_files(CLIENTS_PATH)
    #remove_residual_files(SERVER_PATH)