from motor.motor_asyncio import AsyncIOMotorClient as MotorClient
import sqlite3
from sqlite3 import Cursor




class MongoDatabase(object):
    def __init__(self) -> None:
        self.doc = {}
    
    def update_doc(self,document):
        self.doc = document
    



class PySqliteDatabase(object):
    def __init__(self) -> None:
        self.new_table = Cursor()
    
    def update_table(self,new_table):
        self.table = new_table




