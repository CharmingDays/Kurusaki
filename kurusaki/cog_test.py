import asyncio
import platform
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
    os_name = platform.system()
    path ="D:\GithubRepo\Kurusaki\kurusaki\\bot_info.json"
    if os_name.lower() == "linux":
        path = "bot_info.json"
    bot_info = json.loads(open(path,'r',encoding='utf-8').read())
    await load_command_aliases(bot_info['languages'])

async def load_cogs():
    cogs = ['Cogs.help','Cogs.music','Cogs.events']
    for i in cogs:
        await bot.load_extension(i) 
        print(i)
    await load_bot_info()


def prepare_args(command:commands.Command,ctx:commands.Context):
    commandArgs:typing.Dict = command.params
    userArgs:str = ctx.message.content.replace(f"{ctx.prefix}{ctx.invoked_with} ",'')
    userArgs = userArgs.split(' ')
    if len(userArgs) > len(commandArgs):
        userArgs = " ".join(userArgs)

    return userArgs


@bot.command()
async def some(ctx,*,first):
    await ctx.send(f"This is the first arg {first}")


@bot.command()
async def view(ctx:commands.Context):
    pass


@bot.event
async def on_ready():
    # await load_cogs()
    # await bot.tree.sync()
    print(f'Loaded {bot.user.name}') 
    command = bot.get_command('some')
    command
# bot.run(os.getenv("TEMPEST"))