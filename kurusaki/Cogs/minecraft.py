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


    @commands.hybrid_group(with_app_command=True,description='Minecraft related commands')
    async def mc(self,**kwargs):
        """
        Group for Minecraft commands
        """


    @mc.command(name='connect-rcon',with_app_command=True)
    async def connect_rcon(self,ctx:Context,host:str,port:typing.Optional[int]=25575,*,password:str):
        """
        Setup a RCON connection for  Minecraft related commands for your server members to use.
        {command_prefix}{command_name} host port password
        host(required): The IP address of the minecraft server
        port(optional): The port of the minecraft server. Default is 25575
        password(required): The RCON password for the minecraft server
        {command_prefix}{command_name} 183.125.214.33 RconPassWord
        {command_prefix}{command_name} 183.125.214.33 25580 RconPassWord
        """
        #TODO  Update the database after new changes made
        guildId = str(ctx.guild.id)
        authorId = str(ctx.author.id)
        if password.strip() == "":
            return await self.send_interaction(ctx,"Please include a password")
        
        try:
            async with MinecraftClient(host=host,port=port,password=password) as client:
                if guildId in self.mongoDoc.document['guilds']:
                    await self.send_interaction(ctx,"Replaced previous login with current one.")
                else:
                    await self.send_interaction(ctx,"Saved Minecraft Rcon login.")
                #UPDATE DATABASE
                login = {'host':host,'password':password,'port':port,'owner':authorId,"commands":{}}
                await self.mongoDoc.set_items({f'guilds.{guildId}':login})
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
                return await self.send_interaction(ctx,f'Minecraft account {account["name"]} linked to Discord Account {ctx.author.mention} now')
            if jsonData['id'] == self.mongoDoc.document['accounts'][authorId]['id']:
                return await self.send_interaction(ctx,f'Account {jsonData["name"]} already linked to your Discord account')
            else:
                return await self.send_interaction(ctx,'Replaced previous account {previousAccount} with new account {currentAccount}')
        
        return await self.send_interaction(ctx,f'Minecraft user {username} could not be found, please make sure your spelling is correct.')


    @mc.command(name='add-cmd',with_app_command=True)
    async def add_custom_command(self,ctx:Context,name:str,*,command:str):
        """
        Create a custom discord command for your minecraft server
        {command_prefix}{command_name} cmd-name command
        name(required): The name of the command to create
        command(required): The command to send to the minecraft server
        {command_prefix}{command_name} rain weather rain
        {command_prefix}{command_name} teleport tp @Player1 @Player2 @Player5
        """
        guildId = str(ctx.guild.id)
        userId = str(ctx.author.id)
        if guildId not in self.mongoDoc.document['guilds']:
            return await self.send_interaction(ctx,f"Please setup a Minecraft RCON connection first using the command `{ctx.prefix}mc setup-rcon`")
        ownerId = self.mongoDoc.document['guilds'][guildId]['owner']
        if userId != ownerId:
            return await self.send_interaction(ctx,f'You are not the creator of the RCON connection setup. The person that setup the RCON connection must be the one to crate the custom commands.\nCurrent owner {ctx.guild.get_member(int(ownerId))}')
        
        if name.lower() in self.mongoDoc.document['guilds'][guildId]['commands']:
            return await self.send_interaction(ctx,f'Command {name} already in command list')
        
        #NOTE: Update the database
        await self.mongoDoc.set_items({f'guilds.{guildId}.commands.{name.lower()}':command})
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
        commandList = "\n".join([f"`{name}` - **{command}**" for name, command in commands.items()])
        return await self.send_interaction(ctx, f"Custom Commands:\n{commandList}")


    def check_for_args(self,cmd,args):
        #TODO Check if the command requires arguments and verify the arguments passed if any
        pass


    @mc.command(with_app_command=True)
    async def cmd(self,ctx:Context,name:str,*,args=None):
        """
        Send a pre-defined command to the minecraft server via rcon
        {command_prefix}{command_name} command-name arguments
        arguments(optional): Optional arguments for when the command requires it
        {command_prefix}{command_name} rain
        {command_prefix}{command_name} tp Player1 Player2 Player5
        """
        guildId = str(ctx.guild.id)
        if guildId not in self.mongoDoc.document['guilds']:
            return await self.send_interaction('Minecraft RCON or commands are not setup for this server.')
        if name.lower() not in self.mongoDoc.document['guilds'][guildId]['commands']:
            return await self.send_interaction(ctx,f"Command {name} not found in command list.\nPlease use the command `{ctx.prefix}mc cmd-list` to view commands. or `{ctx.prefix}mc add-cmd` to add a new command.")
        
        command = self.mongoDoc.document['guilds'][guildId]['commands'][name.lower()]
        serverInfo = self.mongoDoc.document['guilds'][guildId]
        async with MinecraftClient(host=serverInfo['host'],port=serverInfo['port'],password=serverInfo['password']) as client:
            return await self.send_interaction(ctx,await client.send(command))

    @mc.command(name='admin-cmd',with_app_command=True)
    async def admin_cmd(self,ctx:Context,*,cmd):
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
        if authorId != self.mongoDoc.document['guilds'][guildId]['owner']:
            return await self.send_interaction(ctx,"You are not the owner of the RCON connection setup for this server.")
        rconInfo = self.mongoDoc.document['guilds'][guildId]
        async with MinecraftClient(host=rconInfo['host'],port=rconInfo['port'],password=rconInfo['password']) as client:
            return await self.send_interaction(ctx,await client.send(cmd))


async def setup(bot):
    await bot.add_cog(Minecraft(bot)) 