import aiohttp 
from discord.ext import commands
import discord
import urllib.parse
from discord.ext.commands import Context

class Anime(commands.Cog):
    def __init__(self,bot):
        self.bot:commands.Bot = bot


    @commands.command(name="imgSearch")
    async def img_search(self,ctx:Context,*,imageUrl:str=None):
        """
        Search for an image on the internet
        {command_prefix}{command_name} imageURL or attachment(uploaded image)
        {command_prefix}{command_name} https://example.com/image.jpg
        """
        if not imageUrl and not ctx.message.attachments:
            return await ctx.send("Please provide an image url or upload an image")
        if not imageUrl and ctx.message.attachments:
            imageUrl = ctx.message.attachments[0].url

        url = "https://api.trace.moe/search?url={}".format(urllib.parse.quote_plus(imageUrl))
        response = await self.fetch("GET",url)
        if response.status == 200:
            trace_data = await response.json()
            if trace_data["result"]:
                data = await self.fetch("GET","https://graphql.anilist.co",json={"query":'query($id: Int){Media(id: $id){title{romaji}episode from image{large}}}',"variables":{"id":trace_data["result"][0]["anilist"]}})
                if data.ok:
                    data = await data.json()
                    data = data["data"]["Media"]
                    embed = discord.Embed(title=data["title"]["romaji"],description="Episode: {}".format(data["episode"]),color=discord.Color.green())
                    embed.set_image(url=data["image"]["large"])
                    return await ctx.send(embed=embed)
            else:
                return await ctx.send("No results found")



    @commands.command()
    async def neko(self,ctx:Context):
        """
        Get a random neko image
        {command_prefix}{command_name}
        """
        response = await self.fetch("GET","https://nekos.life/api/v2/img/neko")
        if response.status == 200:
            data = await response.json()
            embed = discord.Embed(title="Neko",color=discord.Color.random())
            embed.set_image(url=data["url"])
            return await ctx.send(embed=embed)
        return await ctx.send("Failed to fetch image.\nTry again later")
    

    @commands.command(name="randomQuote")
    async def quote(self,ctx:Context,quoteType:str=None,value:str=None):
        """
        Get a random anime quote or from specific character/anime
        {command_prefix}{command_name}
        {command_prefix}{command_name} Luffy
        {command_prefix}{command_name} Death Note
        """
        response_data = {
            "data":None
        }
        if quoteType and quoteType in ['character','anime']:
            if not value:
                if quoteType == "character":
                    return await ctx.send("Please provide character name")
                if quoteType == "anime":
                    return await ctx.send("Please provide anime name")
                
            response = await self.fetch("GET",f"https://animechan.xyz/api/random/{quoteType}?name={value}")
            if response.status == 200:
                response_data["data"] = await response.json()
        elif quoteType and quoteType not in ['character','anime']:
            return await ctx.send("Invalid quote type.\nUse `character` or `anime`")
        
        elif not quoteType:
            response = await self.fetch("GET","https://animechan.xyz/api/random")
            if response.status == 200:
                response_data["data"] = await response.json()
        if not response_data["data"]:
            return await ctx.send("Failed to fetch quote.\nTry again later")
        
        data = response_data["data"]
        embed = discord.Embed(title=data["anime"],description=data["quote"],color=discord.Color.random())
        embed.set_footer(text=data["character"])
        return await ctx.send(embed=embed)
    



async def setup(bot:commands.Bot):
    await bot.add_cog(Anime(bot))