import asyncio
from motor.motor_asyncio import AsyncIOMotorClient as MotorClient
import sqlite3
from sqlite3 import Cursor
import typing
from motor import core as MotorCore
from pymongo import ReturnDocument



class MongoDatabase(object):
    """
    A clas to handle all the database operations for mongodb
    raw_operations/operation: -> {"path.to.key":"value"}
    
    """

    def __init__(self,client:typing.Optional[MotorClient],collection:typing.Optional[MotorCore.AgnosticCollection],document:typing.Optional[typing.Dict]={}):
        self.client:MotorClient = client
        self.collection:MotorCore.AgnosticCollection = collection
        self.document:typing.Dict = document
        self.document_id = {"_id":document['_id']}
        # self.setup_attributes()

    def setup_attributes(self):
        # if self.
        pass
    
    
    def gather_operations(self,operations):
        sorted_operations = {}
        for operation in operations:
            sorted_operations.update(operation)
        
        return sorted_operations


    async def set_items(self,raw_operations:typing.Dict):
        """Add a new key|value pair into the document

        Args:
            raw_operations (Dict): the operations to preform into the document

        Returns:
            None: None

        
        """
        operations = {"$set":raw_operations}
        self.document = await self.collection.find_one_and_update(self.document_id,operations,return_document=ReturnDocument.AFTER)


    async def inc_operation(self,operations:typing.Dict):
        """Increment value of specified key

        Args:
            key_path (str): The path of the key
        """
        self.document = await self.collection.find_one_and_update(self.document_id,operations,return_document=ReturnDocument.AFTER)


    async def rename_key(self,raw_operations:typing.Dict):
        """Rename a specified key

        Args:
            key_path (str): the path to the key to rename
            new_name (str): the new name for the key
        """
        operations = {"$rename":raw_operations}
        self.document =await self.collection.find_one_and_update(self.document_id,operations,return_document=ReturnDocument.AFTER)
    
    async def unset_item(self,raw_operations:str):
        """Remove/unset a key from the dict/document

        Args:
            key_path (str): The dot notation path to the key
        """
        operation = {"$unset":{raw_operations:""}}
        self.document =await self.collection.find_one_and_update(self.document_id,operation,return_document=ReturnDocument.AFTER)
    
    async def append_array(self,operations:typing.Dict):
        """Add an element or elements to an array

        Args:
            array_path (str): The dot notation path of the array
            values (typing.Union[int,str,typing.List]): a list of values or an int to add

        Returns:
            _type_: _description_
        """
        operation = {"$addToSet":operations}
        self.document =await self.collection.find_one_and_update(self.document_id,operation,return_document=ReturnDocument.AFTER)
    

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
        self.document = await self.collection.find_one_and_update(self.document_id,operation,return_document=ReturnDocument.AFTER)

    async def pull_item(self,operations:typing.Dict):
        """Remove an element given specific index

        Args:
            operations (dict): the pull operations to preform

        Returns:
            None
        """
        operation = {"$pull":operations}
        self.document = await self.collection.find_one_and_update(self.document_id,operation,return_document=ReturnDocument.AFTER)


    
    async def custom_operation(self,*operations):
        self.document = await self.collection.find_one_and_update(self.document_id,self.gather_operations(operations),return_document=ReturnDocument.AFTER)

class PySqliteDatabase(object):
    def __init__(self) -> None:
        self.new_table = Cursor()
    
    def update_table(self,new_table):
        self.table = new_table
