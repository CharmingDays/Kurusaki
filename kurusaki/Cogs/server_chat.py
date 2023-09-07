import discord,asyncio,time,random,os
from discord.ext.commands.context import Context
from motor.motor_asyncio import AsyncIOMotorClient as MotorClient
from discord.ext import commands,tasks
from discord.ext.commands import Context



class GuildChat(commands.Cog ):
    """
    chatData --> {
        userId: {"chat":False}
    }
    """
    #enable server-chat (should have timer before disabled)
    #enable server-chat
    
    def __init__(self,bot):
        self.bot:commands.Bot = bot
        self.docId = {"_id":"serverChat"}
        self.webhook_instances = {"_id":"backup"}


    async def connect_mongodb(self):
        self.mongoClient= MotorClient(os.getenv('MONGO'))
        self.mongoCollection = self.mongoClient['Discord-Bot-Database']['General']
        self.mongoDoc = await self.collection.find_one(self.docId)


    async def cog_load(self):
        await self.connect_mongodb()


    async def cog_before_invoke(self, ctx: Context):
        guildId:str = str(ctx.guild.id)
        if guildId not in self.mongoDoc:
            newDoc = {f"{guildId}":{'channel':0,'webhook':0}}
            await self.mongoCollection.update_one(self.docId,{"$set":newDoc})



    async def create_webhook(self,context:Context):
        pass


    @commands.command(name='serverChatOn')
    async def server_chat_on(self,ctx:Context):
        if ctx.guild.id in self.webhook_instances:
            return await ctx.send("Server chat already turned on.")
        
        guildId:str = str(ctx.guild.id)
        channelId = self.mongoDoc[guildId]['channel']
        if channelId:
            hookId = self.mongoDoc[guildId]['webhook']
            for hook in await ctx.guild.webhooks():
                if hook.id == hookId:
                    self.webhook_instances[ctx.guild.id] = hook
                    break
            
            

    @commands.command(name='serverChatChannel')
    async def server_chat_channel(self,ctx:Context,channel:discord.TextChannel):
        guildId:str = str(ctx.guild.id)
        if guildId in self.mongoDoc:
            if str(channel.id) == self.mongoDoc[guildId]['channel']:
                return await ctx.send(f"Server chat channel already set to {channel.mention}.")
            

        self.mongoDoc[guildId]['channel'] = channel.id
        hook = await channel.create_webhook(name='server-chat',reason=f'Server chat webhook created by {self.bot.user.name} for {ctx.author.name}')

        newDoc = {guildId:{'channel':channel.id,'webhook':hook.id}}
        await self.mongoCollection.update_one(self.docId,{"$set":newDoc})
        return await ctx.send(f"Changed server chat channel to {channel.mention}")
        
            




    @commands.Cog.listener('on_message')
    async def serverChatCheck(self,message:discord.Message):
        if message.guild.id in self.webhook_instances:
            pass


async def setup(bot):
    await bot.add_cog(GuildChat(bot))