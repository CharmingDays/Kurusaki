import discord,os
from dotenv import load_dotenv
from discord.ext import commands
import typing
import json
load_dotenv()

bot = commands.Bot(intents=discord.Intents.all(),command_prefix='t.',case_insensitive=True,owner_ids =[185181025104560128,168198926048952320])




async def load_command_aliases(languages:typing.Dict):
    for command_name,language_aliases in languages['Music'].items():
        cmd = bot.get_command(command_name)
        for lang_alias in language_aliases.values():
            if lang_alias['name'] not in cmd.aliases:
                cmd.aliases.append(lang_alias['name'])
                print("Added alias:",lang_alias['name'])
                bot.remove_command(command_name)
                bot.add_command(cmd)


async def load_bot_info():
    bot_info = json.loads(open('D:/GithubRepo/Kurusaki/kurusaki/bot_info.json','r',encoding='utf-8').read())
    # await load_command_aliases(bot_info['languages'])

async def load_cogs():
    cogs = ['Cogs.events','Cogs.help','Cogs.music']
    for i in cogs:
        await bot.load_extension(i) 
        print(i)
    await load_bot_info()


@bot.event
async def on_ready():
    await load_cogs()
    await bot.tree.sync()
    print(f'Loaded {bot.user.name}') 

bot.run(os.getenv("TEMPEST"))