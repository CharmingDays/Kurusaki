import random
import typing
import discord
from aiohttp import ClientSession
from discord.ext import commands
from discord.ext.commands import Context

class RandomGenerator(commands.Cog,name='Random'):
    def __init__(self,bot) -> None:
        self.bot:commands.bot = bot


    async def shuffle_unique_ids(self,amount:int,idList:typing.List):
        """
        Randomly select unique members given an `amount` of memberList  of ids
        """
        newList= []
        for _ in range(0,len(idList)-1):
            if amount == 0:
                return newList

            elem = idList.pop(random.randint(0,len(idList)-1))
            if elem not in newList:
                newList.append(elem)
                amount-=1



    @commands.hybrid_group(name='random',with_app_command=True)
    async def random_group(self,ctx:Context):
        pass


    @random_group.command(with_app_command=True,name='member-from-role')
    async def member_from_role(self,ctx:Context,roles:typing.List[discord.Role],amount:typing.Optional[int]=1):
        """
        Select a random member from given role(s) or from entire server
        roles: The role(s) to select from
        amount(optional): The amount of members to select defaults to 1
        {command_prefix}{command_name} @Super Members @Members 2
        {command_prefix}{command_name} @Members
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
    


    @random_group.command(name='messages')
    async def _messages(self,ctx:Context,channel:typing.Optional[discord.TextChannel],count:typing.Optional[int]=1):
        """
        Randomly select x amount of messages from the past 14 days.
        channel(optional): The channel to select from defaults to current channel
        count(optional): The amount of messages to select defaults to 1 limits to 100
        {command_prefix}{command_name} #general 5
        {command_prefix}{command_name} 5
        {command_prefix}{command_name}
        """
        
        if not channel:
            channel = ctx.channel

        if count > 100:
            return await ctx.send("Please select a number less than 100")
        
        messages = await channel.history(limit=100).flatten()
        

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