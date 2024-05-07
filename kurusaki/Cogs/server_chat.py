import os
import random
import time
import typing
import discord
from discord.ext import commands,tasks
from discord.ext.commands import Context
from .database_handler import MongoDatabase
from motor.motor_asyncio import AsyncIOMotorClient as MotorClient








"""
self.local_chat = {
    "messages":0,
    "guilds":{
        "guild_id": {
            "messages":{"user_id":[time.time(),time.time()]},
            "channel":"discord.TextChannel",
            "channel_id":"discord.TextChannel.id",
        }
    }
}
"""

#{"messages":1,"guilds":{guild_id:{"messages":{"userId:[time.time().time.time()]},timer:"",channel:"",channel_id:""}}}




class GuildChat(commands.Cog ):
    """
    A feature mode that allows users to chat with each other in different servers.
    """
    #enable server-chat (should have timer before disabled)
    #enable server-chat
    
    def __init__(self,bot):
        self.bot:commands.Bot = bot
        self.guild_chat = {}
        self.local_chat = {} 
        self.mongo_doc:MongoDatabase


    async def connect_database(self) -> None:
        client = MotorClient(os.getenv("MONGO"))
        db = client['Discord-Bot-Database']
        collection = db['General']
        doc = await collection.find_one({"_id":"serverChat"})
        self.mongo_doc = MongoDatabase(client,collection,doc)


    # async def cog_load(self):
        # await self.connect_database()
        

    @tasks.loop(minutes=10)
    async def clear_chat(self):
        """
        Clears the chat after a certain time has passed.
        """
        for guild in self.local_chat.copy():
            if guild['timer'] <= time.time():
                channel:discord.TextChannel = guild['channel']
                self.local_chat.pop(guild,None)
                await channel.send("Server chat session timer has expired. Please re-enable server chat to continue chatting.")

                
    def create_message_embed(self,message:discord.Message):
        """Creates and prepares an embed message to be sent."""
        embed = discord.Embed(description=message.content)
        embed.set_footer(text=message.author.name,icon_url=message.author.avatar_url)
        return embed



    @commands.command(name='start-server-chat',aliases=['startserverchat'])
    async def start_server_chat(self,ctx:Context,channel:typing.Optional[discord.TextChannel]):
        """
        Starts the server chat in the channel if specified.
        {command_prefix}{command_name}
        channel(optional): The channel to use for server chat.
        {command_prefix}{command_name} #guild_chats
        """
        guild_id:int = ctx.guild.id
        if guild_id in self.local_chat['guilds']:
            return await ctx.send("Server chat is already enabled.Use stop-server-chat to disable it.")
        
        if channel is None:
            channel = ctx.channel

        self.local_chat['guilds'][guild_id] = {"timer":time.time()+60*10,"channel":channel,"channel_id":channel.id}
        await ctx.send(f"Server chat has been enabled in {channel.mention}. Adding a cooldown for {channel.mention} is recommended.")



    @commands.command(name='stop-server-chat',aliases=['stopserverchat'])
    async def stop_server_chat(self,ctx:Context):
        """
        Stops the server chat.
        {command_prefix}{command_name}
        """
        guild_id:int = ctx.guild.id
        if guild_id not in self.local_chat['guilds']:
            return await ctx.send("Server chat is not enabled.")
        
        self.local_chat['guilds'].pop(guild_id,None)
        await ctx.send("Server chat has been disabled.")


    async def send_server_chat(self,embed:discord.Embed,message:discord.Message):
        """Sends the message to all the servers that have server chat enabled.

        Args:
            embed (discord.Embed): the embed to be sent
            sender_guild_id (int): the guild id of the server that sent the message
        """
        for target_guild in self.local_chat['guilds']:
            if message.guild.id == target_guild:
                continue
            channel:discord.TextChannel = target_guild['channel']
            await channel.send(embed=embed)
            self.local_chat['messages'] += 1
            self.local_chat['guilds'][target_guild]['messages'][message.author.id].append(time.time())





    async def spam_sensor(self):
        """Checks for spam in the server chat."""
        if not self.local_chat['guilds'] or len(self.local_chat['guilds']) < 10 and len(self.local_chat['messages'] < 50):
            return
        

        for guild in self.local_chat['guilds']:
            for user_messages in guild['messages']:
                if len(user_messages) > 5:
                    total_message_delays = sum(user_messages[-10:]) / 10
                    if total_message_delays - user_messages[-10] > 5:
                        #TODO: disable chat or add a cooldown to the user in channel from bot and display warning
                        pass

    @commands.Cog.listener()
    async def on_message(self,message:discord.Message):
        if message.author.bot or message.guild is None or message.guild.id not in self.local_chat:
            return
        
        if message.author.id not in self.local_chat['guilds'][message.guild.id]['messages']:
            self.local_chat['guilds'][message.guild.id]['messages'][message.author.id] = []
        content = self.create_message_embed(message)
        await self.send_server_chat(content,message)



async def setup(bot):
    await bot.add_cog(GuildChat(bot))
