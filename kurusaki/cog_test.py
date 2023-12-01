import discord,os
from dotenv import load_dotenv
from discord.ext import commands
from discord.ext.commands import Context
load_dotenv()

bot = commands.Bot(intents=discord.Intents.all(),command_prefix='t.',case_insensitive=True,owner_ids =[185181025104560128,168198926048952320])




async def load_cogs():
    cogs = ['Cogs.music','Cogs.help']
    for i in cogs:
        await bot.load_extension(i) 
        print(i)

@bot.event
async def on_ready():
    await load_cogs()
    await bot.tree.sync()
    print(f'Loaded {bot.user.name}') 

bot.run(os.getenv("TEMPEST"))