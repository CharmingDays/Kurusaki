import discord,os,time
from motor.motor_asyncio import AsyncIOMotorClient as MotorClient
import requests as rq
from discord.ext import commands
from discord.ext.commands import command
import typing,math
from discord.ext import tasks



class TextChannel(commands.Cog):
    """
    Bot commands to easily and quickly manage your discord text channels
    """
    def __init__(self,bot):
        self.bot = bot
    

    # async def cog_load(self):
        # await self.setup_database()


    async def setup_database(self):
        client = MotorClient(os.getenv("MONGO"))
        database = client['Discord-Bot-Database']
        collection = database['General']
        doc = await collection.find_one({'_id':'text_channels'})
        if doc:
            self.mongoClient=client
            self.mongoCollection=collection
            self.textDoc=doc
        else:
            self.textDoc={}




    @commands.Cog.listener('on_message')
    async def text_channel_messages(self,ctx):
        if ctx.author.bot :
            if str(ctx.channel.id) in self.textDoc['auto-msg-bots'] and ctx.author.id in self.textDoc['auto-msg-bots'][str(ctx.channel.id)]['bots']:
                wait_time = time.time()+self.textDoc['auto-msg-bots'][str(ctx.channel.id)]['wait_time']
                self.botMessages[ctx.message] = wait_time


        
    @commands.has_permissions(manage_channels=True)
    @command(name='cloneTxtChan')
    async def clone_text_channel(self,ctx,channel:typing.Optional[discord.TextChannel],*,newName=None):
        """
        Clone a channel where command is used or of your choice
        channel(optional): The channel to clone
        {command_prefix}{command_name} #general new-general-channel
        """
        if channel is None:
            #if channel argument is not given, set to channel where command is used
            channel = ctx.channel
        
        if newName is None:
            newName = "{channel.name}-clone"
        clone_channel = await ctx.channel.clone(name=newName,reason=ctx.author)
        await clone_channel.send(f"Cloned channel {ctx.channel.name}")


    
    @commands.has_permissions(manage_channels=True)
    @command(name='renameTxtChan')
    async def rename_text_channel(self,ctx,channel:typing.Optional[discord.TextChannel],*,newName=None):
        if channel is None:
            channel = ctx.channel
        if newName is None:
            newName = f"{channel.name}-clone"

        await channel.edit(name=newName,reason=ctx.author)
        return await ctx.send(f"Renamed {channel.name} to {newName}")

    @commands.has_permissions(manage_channels=True)
    @command()
    async def chanTopic(self,ctx:commands.Context,chan:typing.Optional[discord.TextChannel],*,newTopic = None):
        """
        Set or change the topic of a channel
        chanTopic(channel:Optional,newTopic:Required)
        {command_prefix}{command_name} #bot-spam spam your bot commands in here
        """
        if chan is None:
            chan = ctx.channel

        if newTopic is None:
            return await ctx.send(f"Please enter topic details for {chan.mention}")

        await chan.edit(topic=newTopic,reason=ctx.author)

        return await ctx.send(f"{chan.mention}'s new topic set to **{newTopic}**")



    @commands.has_permissions(manage_channels=True)
    @command()
    async def slowMode(self,ctx,chan:typing.Optional[discord.TextChannel],seconds:int = 60):
        """
        Enable slow mode for a channel
        slow-mode(channel:Optional,seconds:Optional)
        {command_prefix}{command_name} #general 60
        `NOTE`: *the seconds can't be in decimal value. Putting 0 Seconds will disable it*
        """
        if chan is None:
            chan = ctx.channel
        
        await chan.edit(slowmode_delay=seconds,reason=ctx.author)
        return await ctx.send(f"Slowmode enabled for {chan.mention} for {seconds} seconds")


    @commands.has_permissions(manage_channels=True)
    @command()
    async def nsfw(self,ctx,chan:typing.Optional[discord.TextChannel],switch = None):
        """
        Turn on or off the NSFW mode for a text channel
        nsfw(chan:Optional,switch:Optional)
        {command_prefix}{command_name} #nsfw-chan on
        `NOTE`: *If no parameters are given, it will set it to the opposite of it's current value (NSFW will be false if initially on)*
        """
        if chan is None:
            chan = ctx.channel

        isNSFW= chan.is_nsfw()
        if switch is None:
            await chan.edit(nsfw=not isNSFW,reason=ctx.author)
            return await ctx.send(f"NSFW mode for {chan.mention} set to {not isNSFW}")

        if switch.lower() == 'on':
            switch = True

        if switch.lower() == 'off':
            switch = False

        if switch != 'on' and switch != 'off':
            return await ctx.send(f"Unknown option {switch}.\nPlease enter `on` or `off` as the parameter")
    
        if isNSFW == switch and isNSFW is True:
            return await ctx.send(f"NSFW mode for {chan.mention} is already on")

        if isNSFW == switch and isNSFW is False:
            return await ctx.send(f"NSFW mode for {chan.mention} is already off")
        
        await chan.edit(nsfw = switch,reason=ctx.author)
        return await ctx.send(f"NSFW mode for {chan.name} set to {switch}")


    @commands.has_permissions(create_instant_invite=True)
    @command(name='channelInvite',aliases=['c-invite'])
    async def channel_invite(self,ctx,channel:typing.Optional[discord.TextChannel],temp="true"):
        """
        Create an instant invite for a text channel
        channel(Optional): The channel to make the invite for, if not provided it will be channel where command is used
        temp(optional):Whether invite should be temporary or not.
        {command_prefix}{command_name} #welcome-members true
        """
        temp=temp.lower()
        if channel is None:
            #if channel argument is not given, set to channel where command is used
            channel = ctx.channel
        if temp == "true":
            temp = True
        else:
            temp = False
        invite_code = await channel.create_invite(temporary=temp,reason=ctx.author)
        await ctx.send(invite_code)



    @commands.command(name='wordHistory')
    async def word_history(self,ctx,past_messages= 200, *, word: str):
        #TODO  TEST THE COMMAND.
        """
        Searches a text channel for a specific word with in last x messages
        past-messages(Optional): Number of messages to check
        word(Required): The word to search
        {command_prefix}{command_name} 250 imposter
        """
        channel = ctx.channel
        raw_messages = await channel.history(limit=past_messages).flatten()
        word_messages= []


        for x in raw_messages:
            if word in x.content:
                word_messages.append(x)

        loopCount = math.ceil(len(word_messages/20))
        for i in range(loopCount):
            emb = discord.Embed(title='Word Search')
            for index, value in enumerate(word_messages.copy()):
                if index > 19:
                    break

                emb.add_field(name=f"{value.content[:10]}...",value=value.jump_url)
                word_messages.pop(index)
            await ctx.send(embed=emb)



    @commands.has_permissions(manage_messages=True)
    @command(name="delMsg",aliases=['del-msg'])
    async def delete_message(self,ctx,channel:typing.Optional[discord.TextChannel],amts=100):
        """
        Deletes x amount of messages in channel where command is used or chosen channel
        channel(optional): The channel to delete messages from, defaults to channel command is used if not provided
        amount(Optional): The amount of messages to delete
        {command_prefix}{command_name} #spam-channel 203
        """
        await ctx.message.delete()
        if channel is None:
            #If channel argument is not given, set to channel where command is used
            channel = ctx.channel
        if amts == 0:
            amts = None

        async for message in channel.history(limit=amts):
            await message.delete()
    


    @commands.has_permissions(manage_messages=True)
    @command()
    async def purge(self,ctx,channel:typing.Optional[discord.TextChannel],amount:typing.Optional[int]=100):
        """
        Deletes given amount (default = 100) of messsages in the channel or selected channel that are less than 14 days old
        {command_prefix}{command_name} channel-name messageAmount
        channel(optional): The chanel to purge. Defaults to channel where command is being used if not provided.
        amount(optional): The amount of messages to purge from the channel. Defaults to 100 if not provided
        {command_prefix}{command_name} #bot-spamming 150
        {command_prefix}{command_name}  150
        """
        await channel.purge(limit=amount)
        
        



    @commands.has_permissions(manage_channels=True)
    @command(name='delChannel')
    async def delete_channel(self,ctx,channel:typing.Optional[discord.TextChannel]):
        if channel is None:
            #If channel argument is not given, set to channel where command is used
            channel = ctx.channel

        name = [channel.name,channel.id]
        await channel.delete()
        if name[1] != ctx.channel.id:
            return await ctx.send(f"Channel {name[0]} has been deleted")
        




async def setup(Kurusaki):
    await Kurusaki.add_cog(TextChannel(Kurusaki))