import random
import typing
import discord
from aiohttp import ClientSession
from discord.ext import commands
from discord.ext.commands import Context

class RandomGenerator(commands.Cog):
    def __init__(self,bot) -> None:
        self.bot:commands.bot = bot


    async def get_unique_ids(self,amount:int,idList:typing.List):
        """
        Randomly select unique members given an `amount` of memberList  of ids
        """
        newList= []
        for _ in range(0,len(idList)):
            if amount == 0:
                return newList

            elem = random.choice(idList)
            if elem not in newList:
                newList.append(elem)
                idList.remove(elem)
                amount-=1



    @commands.hybrid_group(name='random')
    async def random_group(self,ctx:Context):
        pass


    @random_group.command()
    async def member(self,ctx:Context,amount:typing.Optional[int]=1,roles:commands.Greedy[discord.Role]=None):
        """
        Select a random member from given role(s) or from entire server
        """
        if roles:
            memberList= []
            for role in roles:
                memberList.extend(member.id for member in role.members)
            
            if amount ==1:
                memberId = random.choice(memberList)
                return await ctx.send(f"{ctx.guild.get_member(memberId).mention}")
            
            uniqueMembers = [ctx.guild.get_member(memberId).mention for memberId in  await self.get_unique_ids(amount,memberList)]
            return await ctx.send(" ".join(uniqueMembers))
        
        allMemberIds = [member.id for member in ctx.guild.members]
        allMemberIds
        if amount ==1:
            member = random.choice(allMemberIds)
            return await ctx.send(f"{ctx.guild.get_member(member).mention}")

        mentioningMembers = [ctx.guild.get_member(memberId).mention for memberId in await self.get_unique_ids(amount,allMemberIds)]

        return await ctx.send(" ".join(mentioningMembers))
    


    @random_group.command(name='message')
    async def _message(self,ctx:Context,count:typing.Optional[int],channel:typing.Optional[discord.TextChannel]):
        """
        Randomly select x amount of messages from the past 14 days.
        """
        
        if not channel:
            channel = ctx.channel
        if not count:
            pass

    @random_group()
    async def channel(self,ctx:Context,channel:typing.Union[discord.TextChannel,discord.VoiceChannel]):
        if isinstance(channel,discord.VoiceChannel):
            channel = random.choice(ctx.guild.voice_channels)
            return await ctx.send(f"{channel.mention}")
        
        if isinstance(channel,discord.TextChannel):
            channel = random.choice(ctx.guild.text_channels)
            return await ctx.send(f"{channel.mention}")


    @random_group.command()
    async def dice(self,ctx,sides=6):
        """
        Roll a dice and get random number
        sides(optional): The amount of sides the dice should have
        {command_prefix}{command_name} 4
        """
        if sides <2:
            return await ctx.send(f"Please select a number greater than {sides}")

        return await ctx.send(f"**{random.randint(1,sides)}**")

    @random_group.command()
    async def role(self,ctx:Context,amount:int):
        uniqueRoles = await self.get_unique_ids([role.id for role in ctx.guild.roles])
        
        


async def setup(bot:commands.Bot):
    await bot.add_cog(RandomGenerator(bot))