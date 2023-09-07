import discord
from discord.ext import commands
from discord.ext.commands import Cog,command
from motor.motor_asyncio import AsyncIOMotorClient
import os
 
class VoiceEvents(commands.Cog):
    def __init__(self,Kurusaki):
        self.Kurusaki = Kurusaki


    async def connect_database(self):
        client = AsyncIOMotorClient(os.getenv("MONGO"))
        database = client['Discord-Bot-Database']
        collection = database['General']
        doc = await collection.find_one({"_id":"voice"})
        setattr(self,'mongoDoc',doc)
        if not doc:
            setattr(self,'mongoDoc',{"_id":"backup_doc"})
        

    async def setup_hook(self):
        await self.connect_database()


    @Cog.listener('on_voice_state_update')
    async def voice_time_tracker(self,member:discord.Member,before:discord.VoiceState,after:discord.VoiceState):
        """
        This event will track the amount of time a user is connected to a voice channel
        Data:
            - Most/Least time spent by channel
            - Most/Least time spent with user(s)
            - Most/Least time spent by server
            - Most/Lease connected channel
        """
        if before.channel and after.channel != None: #User joins channel
            pass

        if after.channel is None and before.channel: #User disconnected
            pass






def setup(Kurusaki):
    Kurusaki.add_cog(VoiceEvents(Kurusaki))