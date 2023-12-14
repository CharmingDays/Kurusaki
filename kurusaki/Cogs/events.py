import random
import typing
import discord,os
from discord.ext import commands
from discord.ext.commands import Context
from discord.ext.commands.context import Context
from motor.motor_asyncio import AsyncIOMotorClient
from database_handler import MongoDatabase

class ServerEvents(commands.Cog):
    """
    Automate your server by auto adding roles, welcome messages and more!
    """
    def __init__(self,bot):
        self.bot:commands.Bot = bot
        self.docId = {"_id":"serverEvents"}
        self.command_list:typing.List
        self.command_usage:AsyncIOMotorClient
        self.event_document:AsyncIOMotorClient


    async def setup_mongodb_connection(self):
        client = AsyncIOMotorClient(os.getenv("MONGO"))
        database = client['Discord-Bot-Database']
        collection = database['General']
        eventDoc = await collection.find_one({"_id":"serverEvents"})
        command_usage=await collection.find_one({"_id":"command_usage"})
        self.event_document = MongoDatabase(client,collection,eventDoc)
        self.command_usage = MongoDatabase(client,collection,command_usage)



    async def cog_load(self):
        await self.setup_mongodb_connection()
        # self.command_list = self.bot.all_commands()


    async def cog_before_invoke(self, ctx: Context):
        guildId:str = str(ctx.guild.id)
        if guildId not in self.event_document:
            newData = {"welcome_messages":{'messages':[],'channel':0},'auto_roles':[]}
            self.event_document[guildId] = newData
            await self.collection.update_one(self.docId,{"$set":{f"{guildId}":newData}})
            await self.event_document



    async def server_auto_role_handler(self,member:discord.Member):        
        """
        Automatically add roles to members when they join server if roles provided
        """
        guildId:str = str(member.guild.id)
        if guildId in self.event_document:
            guildRoles = self.event_document[guildId]['auto_roles']
            incomingRoles = []
            if guildRoles:
                for roleId in guildRoles:
                    role = member.guild.get_role(roleId)
                    if role:
                        incomingRoles.append(role)
                await member.add_roles(*incomingRoles,reason='Server Auto Role.')



    async def attribute_converter(self,message:str,ctx:Context):
        message:typing.List[str] = list(message)
        for index,word in enumerate(message.copy()):
            if word.startswith('[') and word.endswith(']'):
                newWord = word.replace('[')
                newWord = word.replace(']')
                evalWorld = eval(f"ctx.{newWord}")
                message[index] = evalWorld
        return ' '.join(message)


    async def server_auto_message_handler(self,member:discord.Member):
        """
        Function for handling welcome messages for servers
        """
        guildId:str = str(member.guild.id)
        try:
            welcomeChannelId = self.event_document[guildId]['welcome_messages']['channel']
            if welcomeChannelId:
                channel = member.guild.get_channel(welcomeChannelId)
                message = random.choice(self.event_document[guildId]['welcome_messages']['messages'])
                return await channel.send(message)
        except KeyError as error:
            pass



    @commands.Cog.listener('on_command')
    async def command_use_counter(self,ctx:Context):
        # TODO add handler for if guildId not in database and update the guildId into mongodb
        # TODO validate command names first before adding it into database
        if not ctx.guild:
            # Only for guild commands
            return
        commandName = ctx.command.name.lower()
        guildId = str(ctx.guild.id)
        if commandName not in self.command_usage:
            self.command_usage[commandName] = {"guilds":{guildId:1},"usage":1}



  
  
    async def custom_server_events(self,member:discord.Member):
        if member.guild.id == 298994260810924032:
            await member.edit(nick=member.display_name.lower())

  
    @commands.Cog.listener('on_member_join')
    async def auto_server_events(self,member:discord.Member):
        """
        Member join event listener
        """
        await self.server_auto_role_handler(member)
        await self.server_auto_message_handler(member)



    @commands.has_permissions(manage_roles=True)
    @commands.command(name='serverAutoRole')
    async def server_auto_role(self,ctx:Context,role:discord.Role):
        """
        The role new joining members should be automatically given
        role(required): The role to automatically members when they join
        {command_prefix}{command_name} @Novice Role
        """
        guildId:str = str(ctx.guild.id)
        guildRoles:typing.List[int] = self.event_document[guildId]['auto_roles']
        if role.id in guildRoles:
            return await ctx.send(f"Role **{role.name}** already in auto role list")

        newData = {f"{guildId}.auto_roles":role.id}
        self.event_document[guildId]['auto_roles'].append(role.id)
        await self.collection.update_one(self.docId,{"$push":newData})
        return await ctx.send(f"Added role {role.name} to auto role list")


    async def check_allowed_messages(self,message):
        allowed_attributes = [
            'guild.name',
            'guild.member.count',
            'member.name'
        ]
        newMessage:typing.List[str] = list(message)
        for index,word in enumerate(newMessage.copy()):
            if word.startswith('[') and word.endswith(']'):
                newWorld = word.replace('[')
                newWorld = word.replace(']')
                if newWorld not in allowed_attributes:
                    return newWorld
        return True
    
    @commands.has_permissions(manage_channels=True)
    @commands.command(name='welcomeMessage')
    async def welcome_message(self,ctx:Context,channel:typing.Optional[discord.TextChannel],*,message:str):
        """
        Send a welcome message to new members that join the server
        Use command {command_prefix}messageAttributes to view the lists
        {command_prefix}{command_name} Welcome to [guild.name], [user.mention]. You are the [guild.member.count] member!!
        """

        messageCheck = self.check_allowed_messages(message)
        if messageCheck != True:
            # TODO  provide examples of allowed ones
            return await ctx.send(f"Your welcome message contains attributes that aren't allowed.\n{messageCheck}")
        guildId:str = str(ctx.guild.id)
        savedChannel = self.event_document[guildId]['welcome_messages']['channel']
        if savedChannel:
            # contains content
            if channel and savedChannel != channel.id:
                # update the channel id to a new one
                self.event_document[guildId]['welcome_messages']['channel'] = channel.id
                await self.collection.update_one(self.docId,{"$set":{f"{guildId}.welcome_messages.channel":channel.id}})

        
            self.event_document[guildId]['welcome_messages']['messages'].append(message)
            await self.collection.update_one({"_id":"serverEvents"},{"$push":{f"{guildId}.welcome_messages.messages":message}})
            return await ctx.send(f"Added new message to channel {channel.mention}\n**{message}**")
        
        if not channel:
            channel = ctx.channel
        
        newData = {'channel':channel.id,'messages':[message]}
        self.event_document[guildId]['welcome_messages'] = newData
        await self.collection.update_one(self.docId,{"$set":{f"{guildId}.welcome_messages":newData}})
        return await ctx.send(f"Set {channel.mention} as welcome message channel since no channel provided.\nPlease use the same command with provided channel name and welcome message to change channel.\n")

async def setup(bot:commands.Bot):
    await bot.add_cog(ServerEvents(bot))