import asyncio
import os
import random
import discord
from discord.ext import commands
from discord.ext.commands import Context
from discord.ext.commands.context import Context
from motor.motor_asyncio import AsyncIOMotorClient



class LeagueOfLegends(commands.Cog):
    def __init__(self,bot):
        self.bot:commands.Bot = bot

    async def send_interaction(self,ctx:Context,message):
        if ctx.interaction != None:
            return await ctx.interaction.response.send_message(message)
        
        return await ctx.send(message)

    @commands.hybrid_group(name='league')
    async def league_group(self,ctx:Context):
        """
        The command group for organizing league of legends related commands
        """
    @league_group.command()
    async def link(self,ctx:Context):
        pass

async def setup(bot:commands.Bot):
    await bot.add_cog(LeagueOfLegends(bot))