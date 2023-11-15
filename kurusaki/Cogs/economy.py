import json
import discord,os,time,datetime, asyncio
from discord.ext import commands, tasks
from discord.ext.commands import Cog, command
from motor.motor_asyncio import AsyncIOMotorClient as MotorClient


class Economy(Cog):
    """
    Play the economy game and gain points by messaging or doing daily check in.
    """
    def __init__(self,bot) -> None:
       self.bot = bot



    async def connect_db(self):
        #TODO  setup local database if connection fails and save it 
        client = MotorClient(os.getenv("MONGO"))
        database= client['Discord-Bot-Database']
        collections = database['Economy']
        doc = await collections.find_one("economy")
        setattr(self,'econ',doc)



    @Cog.listener('on_voice_update')
    async def voice_income(self,before,after):
        pass
     

    @Cog.listener('on_message')
    async def user_income(self,msg):
        #TODO  make user income close to real life currency
        points = msg.content.split()/ (len(msg.content.split())/1.5)




async def setup(bot):
    await bot.add_cog(Economy(bot))
