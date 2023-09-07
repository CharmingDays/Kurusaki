import asyncio
import typing
import random
import discord
from discord.ext.commands.context import Context
import openai
import os
from discord.ext import commands
from discord.ext.commands import Cog, command,Context

class Utility(Cog):
    def __init__(self,bot) -> None:
        self.bot:commands.Bot = bot
        self.feed_back_channel_id = 1105158289446142012

    async def load_openai(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")

    async def cog_load(self):
        await self.load_openai()

    # async def cog_command_error(self, ctx: Context, error: commands.CommandError):
    #     if ctx.command.is_on_cooldown(ctx):
    #         cooldown_timer = ctx.command.get_cooldown_retry_after(ctx)
    #         return await ctx.send(f'Command is on cooldown for {cooldown_timer} more seconds')


    @command(name='bugReport')
    async def bug_report(self,ctx,*, message):
        """
        Make a bug report to the developer
        {command_prefix}{command_name}
        {command_prefix}{command_name} The resume command isn't working
        NOTE: Try to include as much info as you can so :)
        """
        #TODO: add to database
        channel = self.bot.get_channel(self.feed_back_channel_id)
        await channel.send(f"`{ctx.author}({ctx.author.id}):` **{message}**")
        await ctx.send(f"Bug report has been sent, thank you for your feedback.!")


    @command(name='requestFeature')
    async def request_feature(self,ctx,*,message):
        """
        Make a feature request to the developer
        {command_prefix}{command_name}
        message: The message to the developer about the feature 
        {command_prefix}{command_name} An anime command for generating random anime titles
        """
        #TODO: add to database
        channel = self.bot.get_channel(self.feed_back_channel_id)
        await channel.send(f"`{ctx.author}({ctx.author.id}):` **{message}**")
        return await ctx.send("Feature request sent!. Thank you.")


    @command()
    async def dice(self,ctx,sides=6):
        """
        Roll a dice and get random number
        sides(optional): The amount of sides the dice should have
        {command_prefix}{command_name} 4
        """
        if sides <2:
            return await ctx.send(f"Please select a number greater than {sides}")

        return await ctx.send(f"**{random.randint(1,sides)}**")




    @commands.Cog.listener('on_message')
    async def chat_gpt_message(self,message:discord.Message):
        if message.author.bot:
            return
        if message.channel.id == 1130492632498442241:
            async with message.channel.typing():
                await asyncio.sleep(3)
            chat = openai.ChatCompletion.create(
                model = 'gpt-3.5-turbo',messages= [{
                    'role':'user','content': message.content
                }]
            )
            content:str = chat['choices'][0]['message']['content']
            if len(content) > 2000:
                halfIndex =(len(content)/2)
                halfContent = content[:halfIndex]
                await message.reply(halfContent)
                return await message.reply(content[halfContent:1])
            return await message.reply(chat['choices'][0]['message']['content'])




    @command(name='randomMember')
    async def random_member(self,ctx,amount=1):
        """
        Pick random member or members
        amount(OPtional): The amount of random members to pick. Defaults to 1 if not provided
        {command_prefix}{command_name} 3
        """
        if amount <= 0:
            return await ctx.send("Amount must be >= 1")
        members = []
        guildMembers = ctx.guild.members
        if amount > len(guildMembers):
            return await ctx.send(f"Random member amount is greater than server members by {amount-len(guildMembers)}")
        def _randomMember(amts):
            if amts == 0:
                return members

            member = random.choice(guildMembers)
            if member not in members:
                members.append(member)
                return _randomMember(amts-1)

            return _randomMember(amts)
        _randomMember(amts=amount)
        return await ctx.send(f"{members}")





    @command(name='randomRoles')
    async def random_roles(self,ctx,amount=1):
        """
        Pick random role/roles from server
        amount(optional): The amount of roles to randomly select
        {command_prefix}{command_name} 3
        """
        def gatherUniqueRoles(currentRoles,selectingRoles,amount):
            newRole = random.choice(currentRoles)
            selectedRoles.add(newRole)
            if len(currentRoles) < amount:
                return gatherUniqueRoles(currentRoles,selectingRoles,amount)
            else:
                return selectedRoles
            
        if amount <= 0:
            return await ctx.send("Amount must be >= 1")
        roles = list(ctx.guild.roles)
        if amount > len(roles):
            await ctx.send(f"Random role amount exceeds server roles by {amount-len(roles)}.")
            amount = amount - len(roles)


        selectedRoles= gatherUniqueRoles(roles,set(),amount)
        return await ctx.send(selectedRoles)

    @command(name='randomWord')
    async def random_word(self,ctx,amount:typing.Optional[int]=1,*,phrase):
        """
        Select random word with in given sentence 
        """
        word = random.choice(list(phrase))
        return await ctx.send(f"**{word}**")
        


    # @commands.hybrid_command(name='schedule_message')
    # async def schedule_message(self,ctx:Context,*,message:str):
    #     await ctx.interaction.response(await select_menu('Days',['1','2']))



async def setup(bot):
    await bot.add_cog(Utility(bot))