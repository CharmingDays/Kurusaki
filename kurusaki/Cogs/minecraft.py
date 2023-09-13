import os
import typing
import discord
from discord.ext.commands.context import Context
from mcrcon import MCRcon
from mcrcon import MCRconException
import time
from discord.ext import commands
from discord.ext.commands import Context
from discord.ext import tasks
import aiohttp
from aiohttp.client_reqrep import ClientResponse
from motor.motor_asyncio import AsyncIOMotorClient as MotorClient

class Minecraft(commands.Cog):
    """
    Minecraft related commands
    """
    def __init__(self,bot):
        self.bot = bot
        self.instances = {}
        self.mc_roles = {}
        self.accounts= {}
        self.mongoDoc= {}
        self.clear_rcon_instances.start()

    
    async def setup_database(self):
        """
        Setup database connection to mongodb and local python sqlite to store linked minecraft accounts to discord
        {discordId:{"uuid":minecraftUUID,"username":Minecraft_Username}}
        """
        client = MotorClient(os.getenv('MONGO'))
        database = client['Discord-Bot-Database']
        collection = database['General']
        doc = await collection.find_one("minecraft")
        self.mongoDoc = doc




    @tasks.loop(minutes=2)
    async def clear_rcon_instances(self):
        """
        Task handler for automatically deleting Minecraft Rcon sessions past 10 minutes
        """
        for userId,container in self.instances.copy().items():
            if time.time() >= container['timer']:
                try:
                    container['client'].disconnect()
                except:
                    # already auto dc
                    pass
                del self.instances[userId]
                print("Deleted connection")

    async def send_interaction(self,ctx:Context,message):
        """
        Send a reply back as interaction only visible to invoker or as regular message if not an interaction
        """
        if ctx.interaction != None:
            return await ctx.interaction.response.send_message(message)
        return await ctx.send(message)


    async def lookup_user(self,username:str):
        url = f"https://api.mojang.com/users/profiles/minecraft/{username}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                await resp.read()
                return resp


    async def cog_before_invoke(self, ctx: Context) -> None:
        instance_required = ['whitelist-user']
        if ctx.command.name in instance_required:
            pass


    @commands.hybrid_group(name='mc')
    async def minecraft_group(self,ctx:Context):
        """
        Group for Minecraft commands
        """


    @minecraft_group.command(name='view-role')
    async def view_role(self,ctx:Context):
        """
        Role that is allowed to use the Minecraft commands
        """
        if ctx.guild.id not in self.mc_roles:
            return self.send_interaction(ctx,f"No required role set yet for **{ctx.guild.name}**")\
        
        role = ctx.guild.get_role(self.mc_roles[ctx.guild.id]['role'])
        return self.send_interaction(ctx,f"Required role for MC commands: **{role.name}**")

    @minecraft_group.command(name='set-role')
    async def set_role(self,ctx:Context,role:discord.Role):
        """
        Sets a Discord role that requires users to have to use minecraft commands
        """
        if ctx.guild.id not in self.mc_roles:
            self.mc_roles[ctx.guild.id] = {'role':role.id}
            return await self.send_interaction(ctx,f"Set role **{role.name}** requirement for Minecraft commands")

        elif role.id == self.mc_roles[ctx.guild.id]['role']:
            return await self.send_interaction(ctx,f"**{role.name}** already set as the required role")

        else:
            self.mc_roles[ctx.guild.id]['role']= role.id
            return await self.send_interaction(ctx,f"Changed role **{role.name}** as new required role for Minecraft commands.")


    @minecraft_group.command(name='setup-rcon')
    async def setup_rcon(self,ctx:Context,host:str,port:typing.Optional[int]=25575,*,password:str):
        """
        Setup a RCON connection for  Minecraft related commands for your server members to use.
        The bot will reconnect or connect to the RCON server using the same credentials provided with this command.
        The bot will use this connection when members use custom commands. EX: daily login for item rewards 
        """
        #TODO: Update the database after new changes made
        guildId = str(ctx.guild.id)
        if password.strip() == "":
            return await self.send_interaction(ctx,"Please include a password")
        
        try:
            client = MCRcon(host=host,password=password,port=port)
            client.connect()
            if guildId in self.mongoDoc['guilds']:
                await self.send_interaction(ctx,"Replaced previous login with current one.")
            else:
                await self.send_interaction(ctx,"Saved Minecraft Rcon login.")
            self.mongoDoc['guilds'][guildId] = {'host':host,'password':password,'port':port,'owner':str(ctx.author.id)}
        except MCRconException as error:
            return await self.send_interaction(ctx,"Failed to connect to the server.\nPlease make sure that your password,IP,port are correct.")




    @minecraft_group.command(name='connect-rcon')
    async def connectRcon(self,ctx:Context,host:str,port:typing.Optional[int]=25575,*,password:str):
        """
        Connect to a minecraft Rcon server
        """
        if password.strip() == "":
            return await self.send_interaction(ctx,'Password not included.')
        try:
            client= MCRcon(host=host,password=password,port=port)
            client.connect()
            self.instances[ctx.author.id]= {'client':client,'timer':time.time()+600}
            return await self.send_interaction(ctx,f'Connected to server.\nBot will auto disconnect in 10 minutes and new connection will have to be established.')
        except MCRconException as error:
            if error.args[0].lower() == "login failed":
                return await self.send_interaction(ctx,'Failed to login, please ensure that the password is correct')
        except (ConnectionRefusedError,TimeoutError) as error:
            print(error)
            return await self.send_interaction(ctx,'Failed to connect to rcon server.\nPlease ensure that the host(ip),port, and password are correct.')



    @minecraft_group.command(name='link-account')
    async def link_account(self,ctx:Context,*,username:str):
        """
        Link your Minecraft account to Discord account to make using commands easier
        """
        account:ClientResponse = await self.lookup_user(username)
        if account.ok:
            jsonData = await account.json()
            if str(ctx.author.id) not in self.mongoDoc['accounts']:
                return await self.send_interaction(ctx,f'Minecraft account {account["name"]} linked to Discord Account {ctx.author.mention} now')
            if jsonData['id'] == self.mongoDoc['accounts'][str(ctx.author.id)]['id']:
                return await self.send_interaction(ctx,f'Account {jsonData["name"]} already linked to your Discord account')
            else:
                return await self.send_interaction(ctx,'Replaced previous account {previousAccount} with new account {currentAccount}')
        
        return await self.send_interaction(ctx,f'Minecraft user {username} could not be found, please make sure your spelling is correct.')


    @minecraft_group.command(name='create-command')
    async def create_command(self,ctx:Context,commandName:str,*,minecraftCommand:str):
        """
        Create a custom discord command for your minecraft server
        Command name must not include spaces (replace it with - or _)
        """
        guildId = str(ctx.guild.id)
        userId = str(ctx.author.id)
        if guildId not in self.mongoDoc['guilds']:
            return await self.send_interaction(ctx,f"Please setup a Minecraft RCON connection first using the command `{ctx.prefix}mc setup-rcon`")
        ownerId = self.mongoDoc['guilds'][guildId]['owner']
        if userId != ownerId:
            return await self.send_interaction(ctx,f'You are not the creator of the RCON connection setup. The person that setup the RCON connection must be the one to crate the custom commands.\nCurrent owner {ctx.guild.get_member(int(ownerId))}')
        
        if commandName.lower() in self.mongoDoc[guildId]['commands']:
            return await self.send_interaction(ctx,f'Command {commandName} already in command list')
        
        self.mongoDoc[guildId]['commands'][commandName.lower()]= minecraftCommand
        #NOTE: Update the database
        return await self.send_interaction(ctx,f"Command {commandName} created as a command for server.")

    @minecraft_group.command(description='disconnect from the mcron server manually')
    async def disconnect(self,ctx:Context):
        """
        Manually disconnect from the rcon server if you don't want to wait until the auto disconnect to kick in.
        """
        if ctx.author.id not in self.instances:
            # Existing connection not found.
            return await self.send_interaction(ctx,'Connection already closed or not found')
        
        client = self.instances[ctx.author.id]['client']
        client.disconnect()
        del self.instances[ctx.author.id]
        return await self.send_interaction(ctx,'Disconnected from rcon server.')

    @minecraft_group.command(name='rcon-cmd')
    async def mc_cmd(self,ctx:Context,*,cmd):
        """
        Send a command to the minecraft server via rcon
        """
        #Check to see if author.id in self.mc_roles to confirm connection
        if ctx.author.id not in self.instances:
            return await self.send_interaction(ctx,f'Please connect to server first with `connect-rcon` command')

        client = self.instances[ctx.author.id]['client']
        return await self.send_interaction(ctx,client.command(cmd))


async def setup(bot):
    await bot.add_cog(Minecraft(bot)) 