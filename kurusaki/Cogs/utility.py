import typing
import discord
from discord.ext.commands.context import Context
from discord.ext import commands
from discord.ext.commands import Cog, command,Context



class Utility(Cog):
    def __init__(self,bot) -> None:
        self.bot:commands.Bot = bot
        self.feed_back_channel_id = 1105158289446142012
        self.utilityDb = {'users':[185181025104560128],'guild':[]}


    @commands.cooldown(rate=5,per=120,type=commands.BucketType.user)
    @command(name='save-quote')
    async def save_quote(self,ctx:Context,msgId:typing.Optional[int]):
        """
        Save a message as a quote for your server members to view later via `view-quote` command
        """
        try:
            message = await ctx.channel.fetch_message(msgId)
            #TODO  Update the message attributes and contents into database
        except Exception as error:
            if isinstance(error,discord.NotFound):
                return await ctx.send(f'Message ID {msgId} does not exist for channel {ctx.channel.mention}')
            if isinstance(error,discord.Forbidden):
                return await ctx.send(f"Bot does not have permission to access the message with ID {msgId}")
            if isinstance(error,discord.HTTPException):
                return await ctx.send("Something went wrong while trying to retrieve the message.\nPlease try again later.")



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


async def setup(bot):
    await bot.add_cog(Utility(bot))