import aiohttp 
from discord.ext import commands
import discord
from discord.ext.commands import Context

class Anime(commands.Cog):
    def __init__(self,bot):
        self.bot:commands.Bot = bot

    


async def setup(bot:commands.Bot):
    await bot.add_cog(Anime(bot))