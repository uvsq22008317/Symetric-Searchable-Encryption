from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


class Database:
    def __init__(self, key=None):
        self.uri = "mongodb+srv://admin:lIhcqsbLFkmnQdhR@mongodbserver.rhvmqyk.mongodb.net/?retryWrites=true&w=majority&appName=mongodbserver"
        self.client = MongoClient(self.uri, server_api=ServerApi('1'))
        self.db =self.client["database"]
        self.collec = self.db["documents"]
        self.index = self.db["index"]



    def addFile(self,text):
        self.collec.insert_one(text)

    def search_word(self,token):
        docs = []
        for t in token:
            query = { "token": t}
            for d in  self.index.find(query, {"doc": 1, "_id": 0}):
             docs.append(d)  
        return docs
    
    # index sous la forme : {'token': '....', 'doc': ['......enc']}
    def addIndex(self,text):
        self.index.insert_many(text)


    
    def searchFile(self,name):
        docs = []
        query = { "name": name}
        for d in self.collec.find(query):
                docs.append(d)
        return docs
