import discord,os,random,json
from discord.ext import commands
from discord.ext.commands import command, Cog
from motor.motor_asyncio import AsyncIOMotorClient as MotorClient
from .database_handler import MongoDatabase
class Guild(Cog,name="Server"):
    """
    Server related commands like change server name, create/delete roles.
    """
    def __init__(self,bot):
        self.bot = bot
        self.mongo:MongoDatabase
        
    async def cog_load(self) -> None:
        await self.connect_database()

    async def connect_database(self):
        client = MotorClient(os.getenv('MONGO'))
        database = client['Discord-Bot-Database']
        collection = database['General']
        doc = await collection.find_one({"_id":"member_join"})
        setattr(self,'mongo',MongoDatabase(client,collection,doc))

    def cog_unload(self):
        #Save data on crash
        with open('event_data.json','w',encoding='utf-8') as file:
            file.write(json.dumps(self.mongo.document))

    @Cog.listener('on_member_join')
    async def member_auto_role(self,member):
        if str(member.guild.id) in self.mongo.document:
            roles = self.mongo.document[str(member.guild.id)]['auto-roles']
            roles = [member.guild.get_role(role) for role in roles]
            return member.add_roles(roles,reason='Automatic role by server.')

    @command(name='auto-role')
    async def auto_role(self,ctx,*roles:discord.Role):
        if str(ctx.guild.id) in self.mongo.document:
            added_roles = []
            for role in roles:
                if role.id not in self.mongo.document[str(ctx.guild.id)]['auto-roles']:
                    self.mongo.document[str(ctx.guild.id)]['auto-roles'].append(role.id)
                    added_roles.append(role.name)
            return await ctx.send(f"Added automatic role(s): **{', '.join(added_roles)}** for new joining members.")
                

        else:
            self.mongo.document[str(ctx.guild.id)] = {
                "auto-roles": [role.id for role in roles]
            }
            return await ctx.send(f"Added automatic role(s) {', '.join([role.name for role in roles])}")
        





    @commands.command(name='create-role')
    @commands.has_permissions(manage_roles=True)
    async def create_role(self, ctx, *, name= None):
        #need to allow authority and colour of the role *still working on it
        """
        create a server role
        __{command_prefix}create_role Server Newbie__
        """
        guild = ctx.guild
        role = await guild.create_role(name=name)
        await ctx.send(f"Role {role.mention} Created")


    @commands.command(name='delete-role')
    @commands.has_permissions(manage_roles=True)
    async def delete_role(self, ctx,* ,name= None):
        """
        delete a server role
        __{command_prefix}delete-role @Role Name__
        """
        guild = ctx.guild
        role = discord.utils.get(guild.roles, name=name)
        try:
            await role.delete()
            await ctx.send(f"{name} deleted")
        except AttributeError:
            await ctx.send(f"{name} is not found")


async def setup(bot):
    await bot.add_cog(Guild(bot))