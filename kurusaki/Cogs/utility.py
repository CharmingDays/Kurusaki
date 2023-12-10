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
        self.utilityDb = {'users':[185181025104560128],'guild':[]}

    async def load_openai(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")

    async def cog_load(self):
        await self.load_openai()

    @Cog.listener('on_command')
    async def command_correction(self,ctx:Context):
        pass

    # async def cog_command_error(self, ctx: Context, error: commands.CommandError):
    #     if ctx.command.is_on_cooldown(ctx):
    #         cooldown_timer = ctx.command.get_cooldown_retry_after(ctx)
    #         return await ctx.send(f'Command is on cooldown for {cooldown_timer} more seconds')

    @commands.cooldown(rate=5,per=120,type=commands.BucketType.user)
    @command(name='save-quote')
    async def save_quote(self,ctx:Context,msgId:typing.Optional[int]):
        """
        Save a message as a quote for your server members to view later via `view-quote` command
        """
        try:
            message = await ctx.channel.fetch_message(msgId)
            #TODO  Update the message attributes and contents into database
            messageData = {'content':message.content,'id':message.id,'author':message.author,'date':message.created_at,'savedBy':ctx.author.id}
            updateFilter = {"$set":{f"{ctx.guild.id}.{message.id}":messageData}}
        except Exception as error:
            if isinstance(error,discord.NotFound):
                return await ctx.send(f'Message ID {msgId} does not exist for channel {ctx.channel.mention}')
            if isinstance(error,discord.Forbidden):
                return await ctx.send(f"Bot does not have permission to access the message with ID {msgId}")
            if isinstance(error,discord.HTTPException):
                return await ctx.send("Something went wrong while trying to retrieve the message.\nPlease try again later.")



    @command(name='autoCorrect')
    async def command_auto_correct(self,ctx:Context,auto_type="guild"):
        guildId = ctx.guild.id
        if auto_type.lower() not in ['guild','user']:
            return await ctx.send(f"Option {auto_type} not found.\nUse option `guild` or `user`.")
        
        if auto_type.lower() == "user" and ctx.author.id not in self.utilityDb['users']:
            self.utilityDb['users'].append(ctx.author.id)
        
        if auto_type.lower() == "guild" and ctx.guild.id not in self.utilityDb['guilds']:
            self.utilityDb['guild'].append(guildId)

        if auto_type.lower() == "guild":
            self.utilityDb[auto_type].remove(guildId)
        else:
            self.utilityDb[auto_type].pop(ctx.author.id)


    @command(name='bugReport')
    async def bug_report(self,ctx,*, message):
        """
        Make a bug report to the developer
        {command_prefix}{command_name}
        {command_prefix}{command_name} The resume command isn't working
        NOTE: Try to include as much info as you can so :)
        """
        #TODO  add to database
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
        #TODO  add to database
        channel = self.bot.get_channel(self.feed_back_channel_id)
        await channel.send(f"`{ctx.author}({ctx.author.id}):` **{message}**")
        return await ctx.send("Feature request sent!. Thank you.")


    @commands.Cog.listener('on_message')
    async def chat_gpt_message(self,message:discord.Message):
        if message.author.bot:
            return
        if message.channel.id == 1130492632498442241:
            async with message.channel.typing():
                await asyncio.sleep(1)
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


async def setup(bot):
    await bot.add_cog(Utility(bot))