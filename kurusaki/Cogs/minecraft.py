import os
import typing
from discord.ext.commands.context import Context
from discord.ext import commands
from discord.ext.commands import Context
import aiohttp
from aiohttp.client_reqrep import ClientResponse
from motor.motor_asyncio import AsyncIOMotorClient as MotorClient
from .minecraft_rcon import MinecraftClient, InvalidPassword, ClientError as RconClientError
from .database_handler import MongoDatabase



class Minecraft(commands.Cog):
    """
    Minecraft related commands
    """
    def __init__(self,bot):
        self.bot = bot
        self.instances = {}
        self.accounts= {}
        self.mongoDoc:MongoDatabase = None

    
    async def setup_database(self):
        """
        Setup database connection to mongodb and local python sqlite to store linked minecraft accounts to discord
        {discordId:{"uuid":minecraftUUID,"username":Minecraft_Username}}
        """
        client = MotorClient(os.getenv('MONGO'))
        database = client['Discord-Bot-Database']
        collection = database['General']
        doc = await collection.find_one("minecraft")
        self.mongoDoc = MongoDatabase(client,collection,doc)


    async def cog_load(self) -> None:
        await self.setup_database()


    async def send_interaction(self,ctx:Context,message,ephemeral:bool=False):
        """
        Send a reply back as interaction only visible to invoker or as regular message if not an interaction
        """
        if ctx.interaction != None:
            return await ctx.interaction.response.send_message(message,ephemeral=ephemeral)
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


    async def update_player_list(self,guild_id:int,list_output:str):
        """
        Update the list of players in the server
        """
        
        # Find the index of the colon
        index = list_output.find(':')
        # Extract the part of the string after the colon, remove leading and trailing whitespace, and split it into a list
        live_players = list_output[index+1:].strip().split(', ')
        player_list = self.mongoDoc.document.get('players',[])
        if not player_list:
            await self.mongoDoc.set_items({f'guilds.{guild_id}.players':live_players})
        
        else:
            for player in live_players.copy():
                if player in player_list:
                    live_players.remove(player)
            await self.mongoDoc.append_array({f'guilds.{guild_id}.players':live_players})


    async def cog_before_invoke(self,ctx:Context):
        if ctx.command.name == 'cmd':
            guildId = str(ctx.guild.id)
            

    
    #TODO Add a check for the command to see if it's on cooldown from custom commands

    @commands.hybrid_group(with_app_command=True,description='Minecraft related commands')
    async def mc(self,**kwargs):
        """
        Group for Minecraft commands
        """


    async def create_guild_data(self,ctx:Context,host:str,password:str,port:int):
        guildId = str(ctx.guild.id)
        authorId = str(ctx.author.id)
        guild_data = {'connection':{'host':host,'password':password,'port':port,'owner':authorId},"commands":{},'players':[]}
        await self.mongoDoc.set_items({f'guilds.{guildId}':guild_data})
        


    @mc.command(name='connect-rcon',with_app_command=True)
    async def connect_rcon(self,ctx:Context,host:str,password:str,port:typing.Optional[int]=25575):
        """
        Setup a RCON connection for  Minecraft related commands for your server members to use.
        {command_prefix}{command_name} host port password
        host(required): The IP address of the minecraft server
        port(optional): The port of the minecraft server. Default is 25575
        password(required): The RCON password for the minecraft server
        {command_prefix}{command_name} 183.125.214.33 RconPassWord
        {command_prefix}{command_name} 183.125.214.33 RconPassWord 25579
        """
        #TODO  Update the database after new changes made
        guildId = str(ctx.guild.id)
        if password.strip() == "":
            return await self.send_interaction(ctx,"Please include a password")
        
        try:
            async with MinecraftClient(host=host,port=port,password=password) as client:
                if guildId in self.mongoDoc.document['guilds']:
                    await self.send_interaction(ctx,"Replaced previous login with current one.")
                else:
                    await self.send_interaction(ctx,"Saved Minecraft Rcon login.")
                #UPDATE DATABASE
                await self.create_guild_data(ctx,host,password,port)
                await self.update_player_list(guildId,await client.send("list"))
        except InvalidPassword as error:
            return await self.send_interaction(ctx,"Failed to connect to the server.\nPlease make sure that your password,IP,port are correct.")

        except RconClientError as error:
            print(error)
            return await self.send_interaction(ctx,"Could not connect to the client")




    @mc.command(name='link-account',with_app_command=True)
    async def link_account(self,ctx:Context,*,username:str):
        """
        Link your Minecraft account to Discord account to make using commands easier
        """
        account:ClientResponse = await self.lookup_user(username)
        authorId = str(ctx.author.id)
        if account.ok:
            jsonData = await account.json()
            if authorId not in self.mongoDoc.document['accounts']:
                await self.mongoDoc.set_items({f'accounts.{authorId}':jsonData})
                return await self.send_interaction(ctx,f'Minecraft account {jsonData["name"]} linked to Discord Account {ctx.author.mention} now')
            elif jsonData['id'] == self.mongoDoc.document['accounts'][authorId]['id']:
                return await self.send_interaction(ctx,f'Account {jsonData["name"]} already linked to your Discord account')
            else:
                await self.mongoDoc.set_items({f'accounts.{authorId}':jsonData})
                return await self.send_interaction(ctx,'Replaced previous account {previousAccount} with new account {currentAccount}')
        
        return await self.send_interaction(ctx,f'Minecraft user {username} could not be found, please make sure your spelling is correct.')


    @mc.command(name='add-cmd',with_app_command=True)
    async def add_command(self,ctx:Context,name:str,command:str,description:typing.Optional[str]=""):
        """
        Create a custom discord command for your minecraft server
        {command_prefix}{command_name} cmd-name command
        name(required): The name of the command to create
        command(required): The command to send to the minecraft server
        {command_prefix}{command_name} rain weather rain
        {command_prefix}{command_name} teleport tp @Player1 @Player2 @Player5
        """
        #@user - Targets the command user (Requires a linked minecraft account)
        guildId = str(ctx.guild.id)
        userId = str(ctx.author.id)
        if guildId not in self.mongoDoc.document['guilds']:
            return await self.send_interaction(ctx,f"Please setup a Minecraft RCON connection first using the command `{ctx.prefix}mc setup-rcon`")
        ownerId = self.mongoDoc.document['guilds'][guildId]['connection']['owner']
        if userId != ownerId:
            return await self.send_interaction(ctx,f'You are not the creator of the RCON connection setup. The person that setup the RCON connection must be the one to crate the custom commands.\nCurrent owner {ctx.guild.get_member(int(ownerId))}')
        
        if name.lower() in self.mongoDoc.document['guilds'][guildId]['commands']:
            return await self.send_interaction(ctx,f'Command {name} already in command list')
        
        #NOTE: Update the database
        await self.mongoDoc.set_items({f'guilds.{guildId}.commands.{name.lower()}':{"command":command,"description":description,"cooldown":0}})
        return await self.send_interaction(ctx,f"Command {name} created as a command for server.")


    @mc.command(name='cmd-list',with_app_command=True)
    async def cmd_list(self, ctx: Context):
        """
        Retrieves the list of custom commands for the guild.
        {command_prefix}{command_name}
        """
        guildId = str(ctx.guild.id)
        if guildId not in self.mongoDoc.document['guilds']:
            return await self.send_interaction(ctx, "Minecraft RCON has not been setup yet.")
        commands = self.mongoDoc.document['guilds'][guildId]['commands']
        if not commands:
            return await self.send_interaction(ctx, "No custom commands have been created yet.")
        commandList = "\n".join([f"`{name}` - **{commandInfo['description']}**" for name, commandInfo in commands.items()])
        return await self.send_interaction(ctx, f"Custom Commands:\n{commandList}")


    def check_for_args(self,ctx:Context,args:str):
        """Check if the command requires arguments and verify the arguments passed if any

        Args:
            ctx (Context): The discord context object
            args (str): The minecraft command to check for arguments

        Returns:
            typing.Dict: The dict response of how the command should be formatted
        """
        #TODO Check if the command requires arguments and verify the arguments passed if any
        user_id:str = str(ctx.author.id)
        guildId = str(ctx.guild.id)
        linked_accounts = self.mongoDoc.document['accounts']
        guild_players = self.mongoDoc.document['guilds'][guildId]['players']
        resp = {}
        conditions = {'success':True}
        if "@user" in args:
            if user_id not in linked_accounts:
                conditions['user'] = False
                conditions['success'] =  False
            else:
                mc_name = linked_accounts[user_id]['name']
                if mc_name in guild_players:
                    resp["@user"] = mc_name

        if conditions['success']:
            for key,value in resp.items():
                args = args.replace(key,value)

        resp['args'] = args
        return resp



    @mc.command(with_app_command=True)
    async def cmd(self,ctx:Context,name:str):
        """
        Send a pre-defined command to the minecraft server via rcon
        {command_prefix}{command_name} command-name arguments
        arguments(optional): Optional arguments for when the command requires it
        {command_prefix}{command_name} time set day
        """

        guildId = str(ctx.guild.id)
        if guildId not in self.mongoDoc.document['guilds']:
            return await self.send_interaction('Minecraft RCON or commands are not setup for this server.')
        if name.lower() not in self.mongoDoc.document['guilds'][guildId]['commands']:
            return await self.send_interaction(ctx,f"Command {name} not found in command list.\nPlease use the command `{ctx.prefix}mc cmd-list` to view commands. or `{ctx.prefix}mc add-cmd` to add a new command.")
        
        command = self.mongoDoc.document['guilds'][guildId]['commands'][name.lower()]
        serverInfo = self.mongoDoc.document['guilds'][guildId]['connection']
        prep_args = self.check_for_args(ctx,command)
        async with MinecraftClient(host=serverInfo['host'],port=serverInfo['port'],password=serverInfo['password']) as client:
            client_resp = await client.send(prep_args['args'])
            return await self.send_interaction(ctx,client_resp)



    #TODO Add cooldown to custom commands



    @mc.command(name='admin-cmd',with_app_command=True)
    async def admin_cmd(self,ctx:Context,*,cmd:str):
        """
        Send a command to the minecraft server via rcon
        {command_prefix}{command_name} minecraft-command
        minecraft-command(required): The command to send to the minecraft server
        {command_prefix}{command_name} time set night
        """
        if not cmd:
            return await self.send_interaction(ctx,"Please include a command to send to the server.")
        guildId = str(ctx.guild.id)
        authorId = str(ctx.author.id)
        if guildId not in self.mongoDoc.document['guilds']:
            return await self.send_interaction(ctx,f"Please setup a RCON connection first using the command `{ctx.prefix}mc connect-rcon`")
        if authorId != self.mongoDoc.document['guilds'][guildId]['connection']['owner']:
            return await self.send_interaction(ctx,"You are not the owner of the RCON connection setup for this server.")
        rconInfo = self.mongoDoc.document['guilds'][guildId]['connection']
        async with MinecraftClient(host=rconInfo['host'],port=rconInfo['port'],password=rconInfo['password']) as client:
            return await self.send_interaction(ctx,await client.send(cmd))


async def setup(bot):
    await bot.add_cog(Minecraft(bot)) 