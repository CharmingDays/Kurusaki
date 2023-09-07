import discord
from discord.ext import commands, tasks
import discord.utils
import os,random
from dotenv import load_dotenv
import os, pymongo
load_dotenv()




extensions = [
    'Cogs.member',
    'Cogs.help',
    'Cogs.music',
    'Cogs.utility',
    'Cogs.events',
    'Cogs.text_channel',
    'Cogs.league'
]




KurusakiIntents = discord.Intents.all()
mongodb = {}
bot_status_types = {
    "playing":discord.ActivityType.playing,
    "listening":discord.ActivityType.listening,
    "watching": discord.ActivityType.watching,
    "streaming": discord.ActivityType.streaming
}



def connect_database():
    client = pymongo.MongoClient(os.getenv("MONGO"))
    database = client['Discord-Bot-Database']
    collections = database['General']
    mongodb['client'] = client
    mongodb['collections'] = collections
    mongodb['doc'] = collections.find_one({"_id":"bot_prefixes"})
    mongodb['status'] = collections.find_one({"_id":"bot_status"})



def get_prefix(bot,ctx):
    guildId = str(ctx.guild.id)
    if ctx.guild is None or guildId not in mongodb['doc']:
        # DM or guild prefixes not defined
        return commands.when_mentioned_or(*['s.'])(bot,ctx)

    guild_prefixes = mongodb['doc'][guildId]
    if guildId in mongodb['doc']:
        return commands.when_mentioned_or(*guild_prefixes)(bot,ctx)

kurusaki = commands.Bot(intents=KurusakiIntents,command_prefix=get_prefix,case_insensitive=True,owner_ids=[185181025104560128])





@kurusaki.event
async def setup_hook():
    connect_database()



@tasks.loop(minutes=15)
async def auto_change_bot_status():
    status_type = random.choice(list(mongodb['status']['kurusaki'].keys()))
    status_message = random.choice(mongodb['status']['kurusaki'][status_type])
    await kurusaki.change_presence(activity=discord.Activity(name=status_message,type=bot_status_types[status_type]))


@auto_change_bot_status.after_loop
async def after_auto_status_loop():
    auto_change_bot_status.change_interval(minutes=random.randint(15,540))


@kurusaki.event
async def on_guild_join(guild:discord.Guild):
    chan = kurusaki.get_channel(1103340937834414100)
    await chan.send(f"{guild.name},{guild.owner}")




@commands.is_owner()
@kurusaki.command(hidden=True)
async def unload_cog(_,*,cog_name):
    await kurusaki.unload_extension(cog_name)


@commands.is_owner()
@kurusaki.command(hidden=True)
async def unload_all_cogs(ctx):
    cogs = [cog.qualified_name for cog in kurusaki.cogs]
    removed = []
    for cog in cogs:
        name = await kurusaki.remove_cog(cog)
        removed.append(name)



@kurusaki.event
async def on_ready():
    print(f'{kurusaki.user.name} is running!',discord.__version__)
    await kurusaki.wait_until_ready()
    auto_change_bot_status.start()
    await load_bot_extensions()
    await kurusaki.tree.sync()
    bot_statuses = mongodb['collections'].find_one({"_id":"bot_status"})['kurusaki']
    status_type = random.choice(list(bot_statuses.keys()))
    message = random.choice(bot_statuses[status_type])
    mongodb['bot-status'] = bot_statuses
    await kurusaki.change_presence(activity=discord.Activity(name=message,type=bot_status_types[status_type]))



@kurusaki.event
async def on_guild_join(guild):
    if str(guild.id) not in mongodb['doc']:
        mongodb['doc'][str(guild.id)] = ['s.']
        mongodb['collections'].update_one({'_id':'bot_prefixes'},{'$set':{str(guild.id):['s.']}})
    


@commands.is_owner()
@kurusaki.command(name='change-bot-status',hidden=True)
async def change_bot_status(ctx,type,*,message):
    await kurusaki.change_presence(activity=discord.Activity(name=message,type=bot_status_types[type]))




@commands.has_permissions(administrator=True)
@kurusaki.command(hidden=True,name='addPrefix')
async def add_prefix(ctx,*,new_prefix:str):
    """
    Make a new prefix for the bot in your server.
    Use underscore(_) to indicate space
    new_prefix(Required): The new additional prefix for the server.
    {command_prefix}{command_name} !@#.
    """
    # check prefix value
    # check if prefix already exist
    if new_prefix is None:
        return await ctx.send("Please enter a prefix to add")
    
    if ctx.guild is None:
        return await ctx.send("Custom Prefixes can only be added for servers.")
    for i in new_prefix:
        if '3' in new_prefix:
            new_prefix=new_prefix.replace('_',' ')
    
    if new_prefix not in mongodb['doc'][str(ctx.guild.id)]:
        mongodb['doc'][str(ctx.guild.id)].append(new_prefix)
    else:
        return await ctx.send(f"Prefix {new_prefix} already existing. NOTE: Bot prefixes are not case sensitive.")
    
    mongodb['collections'].update_one({"_id":"bot_prefixes"},{"$addToSet":{str(ctx.guild.id):new_prefix}})
    return await ctx.send(f"New prefix **{new_prefix}** added for **{ctx.guild.name}**")


@kurusaki.command(name='view-prefixes')
async def view_prefixes(ctx):
    """
    View current prefixes the bot has for the server.
    {command_prefix}{command_name}
    """
    if str(ctx.guild.id) not in mongodb['doc']:
        return await ctx.send("!.")
    return await ctx.send("**{}**".format('\n'.join(mongodb['doc'][str(ctx.guild.id)])))
    



@commands.has_permissions(administrator=True)
@kurusaki.command(name='remove-prefix')
async def remove_prefix(ctx,*,prefix):
    """
    Remove and existing prefix
    prefix(required): The prefix to remove
    {command_prefix}{command_name} !!.
    """

    if prefix is None:
        return await ctx.send("Please enter a prefix to remove.")
    
    prefix = prefix.lower()

    if str(ctx.guild.id) not in mongodb['doc']:
        return await ctx.send(f"No custom prefixes are set for {ctx.guild.name}")
    
    if prefix.lower() not in mongodb['doc'][str(ctx.guild.id)]:
        return await ctx.send(f"Prefix {prefix} does not exist.")
    
    if len(mongodb['doc'][str(ctx.guild.id)]) ==1:
        return await ctx.send("You can not remove the only prefix you have for the bot. Please add a new prefix to remove the old one.")

    index = mongodb['doc'][str(ctx.guild.id)].index(prefix)
    removedPrefix = mongodb['doc'][str(ctx.guild.id)].pop(index)
    mongodb['collections'].update_one({'_id':'bot_prefixes'},{'$pull':{str(ctx.guild.id):{"$in":[prefix]}}})
    return await ctx.send(f"Removed prefix **{removedPrefix}** for **{ctx.guild.name}**")




async def load_bot_extensions():
    for ext in extensions:
        await kurusaki.load_extension(ext)
        print(ext)



# Run testing app Kurusaki Kurusaki
kurusaki.run(os.getenv("KURUSAKI"))