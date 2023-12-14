import asyncio
from motor.motor_asyncio import AsyncIOMotorClient as MotorClient
import sqlite3
from sqlite3 import Cursor
import typing
from motor import core as MotorCore




class MongoDatabase(object):
    def __init__(self,client:typing.Optional[MotorClient],collection:typing.Optional[MotorCore.AgnosticCollection],document:typing.Optional[typing.Dict]={}):
        self.client:MotorClient = client
        self.collection:MotorCore.AgnosticCollection = collection
        self.document:typing.Dict = document
        self.document_id = {"_id":document['_id']}
        self.setup_attributes()

    def setup_attributes(self):
        # if self.
        pass
    
    
    def gather_operations(self,operations):
        sorted_operations = {}
        for operation in operations:
            sorted_operations.update(operation)
        
        return sorted_operations


    async def set_item(self,raw_operations):
        operations = {"$set":self.gather_operations(raw_operations)}
        return await self.collection.update_one(self.document_id,operations)

    async def inc_operation(self,key_path:str,inc_by:int):
        operation = {"$inc":{key_path:inc_by}}
        return await self.collection.update_one(self.document_id,operation)

    async def rename_key(self,key_path:str,new_name:str):
        operation = {"$rename":{key_path:new_name}}
        return await self.collection.update_one(self.document_id,operation)
    
    async def unset_item(self,key_path):
        operation = {"$unset":{key_path:""}}
        return await self.collection.update_one(self.document_id,operation)
    
    async def append_array(self,array_path,values:typing.Union[int,str,typing.List]):
        """Add an element or elements to an array

        Args:
            array_path (str): The dot notation path of the array
            values (typing.Union[int,str,typing.List]): a list of values or an int to add

        Returns:
            _type_: _description_
        """
        operation = {"$addToSet":{array_path:values}}
        return await self.collection.update_one(self.document_id,operation)
    

    async def pop_array(self,array_path,first_or_last:int):
        """
        Remove the first or last element of the array

        Args:
            array_path (int): The dot notation path of the array
            first_or_last (int): 1 to remove last and -1 to remove the first

        Returns:
            pymongo.results.UpdateResult: An instance of the pymongo.results.UpdateResult
        """
        operation = {"$pop":{array_path:first_or_last}}
        return await self.collection.update_one(self.document_id,operation)

    async def pull_item(self,array_path:str,index:int):
        """Remove an element given specific index

        Args:
            array_path (str): The dot notation path of the array 
            index (int): the index of the element in the array

        Returns:
            _type_: The pymongo.results.UpdateResult
        """
        operation = {"$pull":{array_path:{"$position":index}}}
        return await self.collection.update_one(self.document_id,operation)
    

    
    async def custom_operation(self,*operations):        
        return await self.collection.update_one(self.document_id,self.gather_operations(operations))


class PySqliteDatabase(object):
    def __init__(self) -> None:
        self.new_table = Cursor()
    
    def update_table(self,new_table):
        self.table = new_table


