import asyncio
import os
import random
import typing
import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands import Context
from discord.ext.commands.context import Context
from motor.motor_asyncio import AsyncIOMotorClient
from .wrappers.league import Summoner


class LeagueOfLegends(commands.Cog):
    def __init__(self,bot):
        self.bot:commands.Bot = bot
        self.summoner = Summoner(os.getenv("RIOT_API_KEY"))

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
    async def link_account(self,ctx:Context,riot_name:str,tag:str):
        try:
            resp:typing.Dict = await self.summoner.get_user_by_riot_id(riot_name,tag=tag)
            linking = await self.summoner.verify_summoner(resp["puuid"])
        except aiohttp.ClientResponseError as e:
            print(e)
            return await self.send_interaction(ctx,f"Could not verify summoner, please try again and check your spellings")
        else:
            if linking
        

async def setup(bot:commands.Bot):
    await bot.add_cog(LeagueOfLegends(bot))