import discord,os,asyncio
from discord.ext.commands import Context
from discord.ext import commands,tasks




class OceanBottle(commands.Cog):
    def __init__(self,bot) -> None:
        self.bot:commands.Bot = bot

    
    
    @commands.Cog.listener('on_command')
    async def bottle_generator(self,ctx:Context):
        pass



async def setup(bot:commands.Bot):
    await bot.add_cog(OceanBottle(bot))