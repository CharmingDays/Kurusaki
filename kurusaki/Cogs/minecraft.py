import typing
import discord
from discord.ext.commands.context import Context
from mcrcon import MCRcon
from mcrcon import MCRconException
import time
from discord.ext import commands
from discord.ext.commands import Context
from discord.ext import tasks
import requests as rq


class Minecraft(commands.Cog):
    """
    Minecraft related commands
    """
    def __init__(self,bot):
        self.bot = bot
        self.instances = {}
        self.mc_roles = {}
        self.clear_rcon_instances.start()
        self.accounts= {}

    
    async def setup_database(self):
        """
        Setup database connection to mongodb and local python sqlite to store linked minecraft accounts to discord
        {discordId:{"uuid":minecraftUUID,"username":Minecraft_Username}}
        """
        pass




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
        data = rq.get(url)
        if data.ok:
            return data.json()

        return False


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
        Setup a RCON connection for the Minecraft related commands to use later.
        The bot will reconnect or connect to the RCON server using the same credentials provided with this command.
        Commands like `whitelist-user` and `block-user` will reuse the connection credentials
        """
        # if password.strip() == "":
        #     return await self.send_interaction(ctx,'Password not included.')
        # try:
        #     client= MCRcon(host=host,password=password,port=port)
        #     client.connect()
        #     self.instances[ctx.author.id]= {'client':client,'timer':time.time()+600}
        #     return await self.send_interaction(ctx,f'Connected to server.\nBot will auto disconnect in 10 minutes and new connection will have to be established.')
        # except MCRconException as error:
        #     if error.args[0].lower() == "login failed":
        #         return await self.send_interaction(ctx,'Failed to login, please ensure that the password is correct')
        # except (ConnectionRefusedError,TimeoutError) as error:
        #     print(error)
        #     return await self.send_interaction(ctx,'Failed to connect to rcon server.\nPlease ensure that the host(ip),port, and password are correct.')




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
        account = await self.lookup_user(username)
        if  account != False:
            if str(ctx.author.id) not in self.accounts:
                return await self.send_interaction(ctx,f'Minecraft account {account["id"]} linked to Discord Account {ctx.author.mention} now')

        return await self.send_interaction(ctx,f'Minecraft user {username} could not be found, please make sure your spelling is correct.')


    # @minecraft_group.command()
    # async def whitelist_user(self,ctx:Context,*,user:typing.Union[discord.Member,str]):
    #     if type(user) == discord.Member:
    #         if str(ctx.author.id) not in self.accounts:
    #             return await self.send_interaction(ctx,f"Server member {user.name} does not have a linked Minecraft account.\nPlease use their Minecraft username instead or have them link one prior to the command usage.")





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

    @minecraft_group.command(name='mc-cmd')
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