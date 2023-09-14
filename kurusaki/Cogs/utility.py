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


async def setup(bot):
    await bot.add_cog(Utility(bot))