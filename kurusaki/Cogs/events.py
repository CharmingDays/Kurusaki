import asyncio
import random
import time
import typing
import discord,os
from discord.ext import commands
from discord.ext.commands import Context
from discord.ext.commands.context import Context
from motor.motor_asyncio import AsyncIOMotorClient
from .database_handler import MongoDatabase
from googletrans import Translator

class ServerEvents(commands.Cog):
    """
    Automate your server by auto adding roles, welcome messages and more!
    """
    def __init__(self,bot):
        self.bot:commands.Bot = bot
        self.command_usage:MongoDatabase
        self.event_document:MongoDatabase
        self.translator = Translator()
        self.reply_queue:typing.Dict = {}


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
        if guildId not in self.event_document.document:
            await self.event_document.set_items({"welcome_messages":{'messages':[],'channel':0},'auto_roles':[]})



    async def server_auto_role_handler(self,member:discord.Member):        
        """
        Automatically add roles to members when they join server if roles provided
        """
        guildId:str = str(member.guild.id)
        if guildId in self.event_document.document:
            guildRoles = self.event_document.document[guildId]['auto_roles']
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
            welcomeChannelId = self.event_document.document[guildId]['welcome_messages']['channel']
            if welcomeChannelId:
                channel = member.guild.get_channel(welcomeChannelId)
                message = random.choice(self.event_document.document[guildId]['welcome_messages']['messages'])
                return await channel.send(message)
        except KeyError as error:
            pass



    @commands.Cog.listener('on_command')
    async def command_use_counter(self,ctx:Context):
        if not ctx.guild:
            # Only for guild commands
            return
        command_name = ctx.command.name.lower()
        guildId = str(ctx.guild.id)
        if command_name in self.command_usage.document:
            operations = {"$inc":{f"{command_name}.usage":1,f"{command_name}.guilds.{guildId}":1}}
            await self.command_usage.inc_operation(operations)
        
        else:
            await self.command_usage.set_items({command_name:{'usage':1,'guilds':{guildId:1}}})

        


    def calculate_cosine_similarity(self,word1, word2):
        # Tokenize words
        tokens1 = set(word1.lower())
        tokens2 = set(word2.lower())

        # Create a set of unique tokens
        unique_tokens = tokens1.union(tokens2)

        # Create vectors for each word
        vector1 = [1 if token in tokens1 else 0 for token in unique_tokens]
        vector2 = [1 if token in tokens2 else 0 for token in unique_tokens]

        # Calculate the dot product
        dot_product = sum(a * b for a, b in zip(vector1, vector2))

        # Calculate the magnitude of each vector
        magnitude1 = sum(a**2 for a in vector1) ** 0.5
        magnitude2 = sum(a**2 for a in vector2) ** 0.5

        # Calculate the cosine similarity
        if magnitude1 == 0 or magnitude2 == 0:
            return 0  # Avoid division by zero
        else:
            similarity = dot_product / (magnitude1 * magnitude2)
            return similarity


    def loop_all_commands(self,target):
        word_vector = {'vector':0,'command_name':''}
        for command_name in self.bot.all_commands:
            vector = self.calculate_cosine_similarity(command_name,target)
            if vector > word_vector['vector']:
                word_vector['vector'] = vector
                word_vector['command_name'] = command_name
        return word_vector

    def detect_language(self,command_name):
        language = self.translator.detect(command_name)
        if isinstance(language.lang,list):
            if language[1].lower() == 'zh-cn':
                return 'mandarin'
        elif language.lang.lower() == 'zh-cn':
            return 'mandarin'


    async def send_translated_correction(self,ctx:Context,command_name:str):
        language = self.detect_language(command_name)
        suggest_command = self.loop_all_commands(command_name)
        return await ctx.send(f"{suggest_command}")



    def prepare_help_doc(self,ctx:Context,command:commands.Command) ->discord.Embed:
        doc = command.help
        doc= doc.replace("{command_prefix}",ctx.prefix)
        doc = doc.replace("{command_name}",command.name)
        aliases = f"{ctx.prefix}".join(command.aliases)
        if command.aliases:
            emb = discord.Embed(title=f"{ctx.prefix}{command.name} **|** {ctx.prefix}{aliases}",description=doc,color=discord.Color.random())
            return emb
    
        emb=discord.Embed(description=f"{ctx.prefix}{command.name}\n{doc}",color=discord.Color.random())
        return emb


    async def queue_msg_reply(self,ctx,timeout,messages:typing.List):
        authorId = ctx.author.id
        self.reply_queue[authorId] = {'replied':False,'messages':messages,'timeout':time.time()+timeout}
        while timeout > 0:
            if self.reply_queue[authorId]['replied']:
                self.reply_queue.pop(authorId)
                return True
            await asyncio.sleep(1)
            timeout-=1

        raise asyncio.TimeoutError
    

    @commands.Cog.listener('on_message')
    async def wait_for_message_reply(self,msg:discord.Message):
        authorId = msg.author.id
        if authorId in self.reply_queue:
            if msg.content.lower() in self.reply_queue[authorId]['messages']:
                self.reply_queue[authorId]['replied'] = True
        

    @commands.Cog.listener('on_reaction_add')
    async def wait_for_reaction_reply(self,reaction:discord.Reaction,user:typing.Union[discord.Member,discord.User]):
        authorId = user.id
        if authorId in self.reply_queue:
            if str(reaction.emoji) in self.reply_queue[authorId]['messages']:
                self.reply_queue[authorId]['replied'] = True


    @commands.Cog.listener('on_command_error')
    async def auto_correct_suggestion(self,ctx:Context,error):
        # TODO add threshold for what is a good correction
        command_name = ctx.invoked_with
        if isinstance(error,commands.CommandNotFound):
            suggestion_vector = self.loop_all_commands(command_name)
            if suggestion_vector and ctx.author.id in self.bot.owner_ids:
                msg = await ctx.send(f"Did you mean {suggestion_vector['command_name']}")
                await msg.add_reaction('👍')
                try:
                    await self.queue_msg_reply(ctx,15,['yes','y','👍'])
                except asyncio.TimeoutError:
                    await msg.remove_reaction(emoji='👍',member=self.bot.user)
                    await msg.delete()
                else:
                    separator:str = ctx.message.content.find(' ')
                    command_name:commands.Command =self.bot.get_command(suggestion_vector['command_name'])
                    if suggestion_vector['command_name'].lower() == 'help' and separator != -1:
                        target_command:commands.Command = self.bot.get_command(ctx.message.content[separator+1:])
                        command_embed = self.prepare_help_doc(ctx,target_command)
                        return await ctx.send(embed=command_embed)
                    if separator == -1:
                        await ctx.invoke(command_name)
                        
                    # TODO add the provided args if any
                    # TODO prepare param values and eval it into ctx.invoke(command_name,arg1,arg2)
  
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
        if not ctx.guild:
            return await ctx.send("This command can only be used in servers.")
        guildId:str = str(ctx.guild.id)
        guildRoles:typing.List[int] = self.event_document.document[guildId]['auto_roles']
        if role.id in guildRoles:
            return await ctx.send(f"Role **{role.name}** already in auto role list")

        self.event_document.document[guildId]['auto_roles'].append(role.id)
        await self.event_document.append_array({f"{guildId}.auto_roles":role.id})
        return await ctx.send(f"Added role {role.name} to auto role list")


    async def check_allowed_messages(self,message):
        allowed_attributes = [
            'guild.name',
            'guild.member.count',
            'member.name'
        ]
        newMessage:typing.List[str] = list(message)
        for word in newMessage.copy():
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
        savedChannel = self.event_document.document[guildId]['welcome_messages']['channel']
        if savedChannel:
            # contains content
            if channel and savedChannel != channel.id:
                # update the channel id to a new one
                await self.event_document.set_items({f"{guildId}.welcome_messages.channel":channel.id})

        
            await self.event_document.append_array({f"{guildId}.welcome_messages.messages":message})
            return await ctx.send(f"Added new message to channel {channel.mention}\n**{message}**")
        
        if not channel:
            channel = ctx.channel
        
        newData = {'channel':channel.id,'messages':[message]}
        await self.event_document.set_items({f"{guildId}.welcome_messages":newData})
        return await ctx.send(f"Set {channel.mention} as welcome message channel since no channel provided.\nPlease use the same command with provided channel name and welcome message to change channel.\n")

async def setup(bot:commands.Bot):
    await bot.add_cog(ServerEvents(bot))