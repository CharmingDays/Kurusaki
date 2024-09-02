import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient as MotorClient
from pymongo import MongoClient
import sqlite3
from sqlite3 import Cursor
import typing
from motor import core as MotorCore
from pymongo import ReturnDocument
import uuid
import json






class MusicSqlite(object):
    """
    A class to handle all the database operations for sqlite3 and is used for backup when connection is lost to mongodb or other main database
    """
    def __init__(self) -> None:
        self.new_table = Cursor()
    
    def update_table(self,new_table):
        self.table = new_table



class MusicMongo(object):
    def __init__(self):
        self.client:MongoClient = MotorClient(os.getenv("MONGO"))
        self.database:MotorCore.AgnosticDatabase = self.client['Discord-Bot-Database']
        self.collection:MotorCore.AgnosticCollection = self.database['General']
        self.document:typing.Dict[typing.Any,typing.Any]
        self.doc_id = {"_id":"music"}


    async def load_document(self):
        music_doc = await self.collection.find_one({"_id":"music"})
        if music_doc:
            self.document = music_doc
            self.doc_id['_id'] = music_doc['_id']
        else:
            self.document = {}


    async def change_volume(self,guild_id:int,volume:int):
        await self.collection.find_one_and_update(self.doc_id,{"$set":{f"{guild_id}.vol":volume}},return_document=ReturnDocument.AFTER)


    async def remove_song(self,user_id:int,song:str):
        await self.collection.find_one_and_update(self.doc_id,{"$pull":{f"userPlaylist.{user_id}":song}},return_document=ReturnDocument.AFTER)


    async def save_song(self,user_id:int,track_info:typing.Dict):
        if user_id not in self.document['userPlaylist']:
            await self.collection.find_one_and_update(self.doc_id,{"$set":{f"userPlaylist.{user_id}":[track_info]}},return_document=ReturnDocument.AFTER)
        else:
            await self.collection.find_one_and_update(self.doc_id,{"$push":{f"userPlaylist.{user_id}":track_info}},return_document=ReturnDocument.AFTER)

