import random
import time
from motor.motor_asyncio import AsyncIOMotorClient as MotorClient,AsyncIOMotorCollection as MotorCollection
from discord.ext.commands import Context
from discord.ext import commands
import os



class OceanBottle(commands.Cog):
    def __init__(self,bot) -> None:
        self.bot:commands.Bot = bot
        self.mongoDoc = {}
        self.collections:MotorCollection = None


    async def cog_load(self) -> None:
        await self.setup_mongodb()

    async def setup_mongodb(self):
        client = MotorClient(os.getenv("MONGO"))
        database = client['Discord-Bot-Database']
        collection = database['General']
        doc = await collection.find_one("ocean_bottle")
        self.mongoDoc = doc
        self.collections = collection
        print("Ocean bottle loaded")


    def cooldown_remainder(self,seconds):
        if seconds > 60 and seconds < 3600:
            minutes = seconds/60
            return f"{int(minutes)} minutes"
        if seconds > 3600:
            hours = (seconds/60)/60
            return f"{round(hours,2)} hours"

    
    async def remove_local_bottle(self,userId:str,date:str):
        for index,bottle in enumerate(self.mongoDoc['bottles'].copy()):
            if bottle['userId'] == userId and bottle['date'] == date:
                del self.mongoDoc['bottles'][index]
                return True
            
        return False

    async def remove_bottle(self,bottle):
        updateFilter = {"$pull":{"bottles":bottle}}
        try:
            await self.collections.update_one({"_id":"ocean_bottle"},updateFilter)
            await self.remove_local_bottle(bottle['userId'],bottle['date'])
            return True
        except:
            return False

    async def bottle_generator(self):
        #TODO: Auto calibrate the randomRange with frequency of commands being used
        randomRange = random.choice(len(self.mongoDoc['bottles'])*100)
        try:
            message =self.mongoDoc['bottles'][randomRange]
            return message
        except IndexError:
            return False

    @commands.Cog.listener('on_command')
    async def bottle_generator(self,ctx:Context):
        bottle = self.bottle_generator()
        if isinstance(bottle,str):
            # TODO:Make message better embedded
            await self.remove_bottle(bottle)
            return ctx.author.send(bottle)



    @commands.cooldown(type=commands.BucketType.user,rate=3,per=3600)
    @commands.command(name='throw-bottle')
    async def throw_bottle(self,ctx:Context,*,message:str):
        if message.strip() == "":

            return await ctx.send("Please include an attached message on your bottle.")

        bottle = {
            "message":message,
            "userId":str(ctx.author.id),
            "date":str(time.time())
        }
        self.mongoDoc['bottles'].append(bottle)
        updateFilter = {"$push":{"bottles":bottle}}
        await self.collections.update_one({"_id":"ocean_bottle"},updateFilter)
        return await ctx.send("Your message has been sent floating into the Discord Ocean, and hopefully someone will find it. :)")


    @throw_bottle.error
    async def throw_bottle_error(self,ctx:Context,error):
        if isinstance(error,commands.CommandOnCooldown):
            return await ctx.send(f"You are on cooldown for {self.cooldown_remainder(error.retry_after)} before you can use this command again.")


async def setup(bot:commands.Bot):
    await bot.add_cog(OceanBottle(bot))