import asyncio
import os
import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands import Context


class Animals(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cat_api_headers = {
            'x-api-key':os.getenv('THE_CAT_API_KEY')
        }
    

    @commands.command(name="cat-fact",aliases=["catfact"])
    async def cat_fact(self,ctx:Context):
        """
        Get a random cat fact
        """
        async with aiohttp.ClientSession() as session:
            async with session.get("https://catfact.ninja/fact") as response:
                data = await response.json()
                return await ctx.send(data['fact'])
            

    @commands.command(name="cat-pic",aliases=["catpic"])
    async def dog_pic(self,ctx:Context):
        """
        Get a random cat picture
        """
        async with aiohttp.ClientSession(headers=self.cat_api_headers) as session:
            async with session.get("https://api.thecatapi.com/v1/images/search") as response:
                data = await response.json()
                return await ctx.send(data[0]['url'])
            

    
    @commands.command(name="dog-fact",aliases=["dogfact"])
    async def dog_fact(self,ctx:Context):
        """
        Get a random dog fact
        """
        async with aiohttp.ClientSession() as session:
            async with session.get("https://dogapi.dog/api/v2/facts") as response:
                data = await response.json()
                return await ctx.send(data['data']['attributes']['body'])   
            

    @commands.command(name="dog-pic",aliases=["dogpic"])
    async def dog_pic(self,ctx:Context):
        """
        Get a random cat picture
        """
        async with aiohttp.ClientSession(headers=self.cat_api_headers) as session:
            try:
                async with session.get("https://api.thedogapi.com/v1/images/search") as response:
                    if response.ok:
                        data = await response.json()
                        url = data[0]['url']
                    else:
                        async with session.get("https://random.dog/woof.json") as response:
                            data = await response.json()
                            url = data['url']
                    return await ctx.send(url)
            except Exception as e:
                print(e)
                return await ctx.send("An error occured while fetching the image")



    @commands.command()  
    async def shibe(self,ctx:Context):
        """
        Get a random shibe picture
        """
        async with aiohttp.ClientSession() as session:
            async with session.get("http://shibe.online/api/shibes?count=1&urls=true&httpsUrls=true") as response:
                data = await response.json()
                return await ctx.send(data[0])
            
    @commands.command(name="fox-pic",aliases=["foxpic"])
    async def fox_pic(self,ctx:Context):
        """
        Get a random fox picture
        """
        async with aiohttp.ClientSession() as session:
            async with session.get("https://randomfox.ca/floof/") as response:
                data = await response.json()
                return await ctx.send(data['image'])
            
    

    @commands.command(name="duck-pic",aliases=["duckpic"])
    async def duck_pic(self,ctx:Context):
        """
        Get a random duck picture
        """
        urls = ["https://random-d.uk/api","https://random-d.uk/api/v2"]
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{urls[0]}/random") as response:
                if response.ok:
                    data = await response.json()
                    url = data['url']

                else:
                    async with session.get(f"{urls[1]}/random") as response:
                        data = await response.json()
                        url = data['url']
                        
                return await ctx.send(url)



async def setup(bot):
    await bot.add_cog(Animals(bot))