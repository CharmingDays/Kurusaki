import discord
from discord.ext import commands
from discord.ext.commands import command
import json
from googletrans import Translator
import platform

class MyHelpCommand(commands.MinimalHelpCommand):
    def __init__(self, **options) -> None:
        self.detector = Translator()
        super().__init__(**options)
        self.command_attrs['aliases'] = ['도움'] #Help command aliases
        self.load_bot_info()

    def load_bot_info(self):
        os_name = platform.system()
        path ="D:\GithubRepo\Kurusaki\kurusaki\\bot_info.json"
        if os_name.lower() == "linux":
            path = "bot_info.json"
        file = json.loads(open(path,encoding='utf-8').read())
        setattr(self,'lang',file['languages'])
        setattr(self,'hidden_func',file['hidden'])


    async def send_bot_help(self, command):
        emb = discord.Embed(color=discord.Color.random(), title="Help Commands", description=f"For a list of command cogs __{self.context.prefix}cogs__\nFor help with a specific command __{self.context.prefix}help Command Name__\nFor a list of commands in a specific cog __{self.context.prefix}help cog name__\n__{self.context.prefix}addPrefix NewPrefix__\n\n\n[Invite Bot](https://discordapp.com/oauth2/authorize?client_id={self.context.bot.user.id}&scope=bot&permissions=8) | [Bot Server](https://discord.gg/CpcW8UyhfD)")
        emb.set_thumbnail(url=self.context.bot.user.display_avatar.url)
        if self.context.guild.icon is None:
            emb.set_footer(icon_url="https://cdn.discordapp.com/attachments/671263788862930964/904594760675774464/NA_ICON.png",text=self.context.guild.name)
        else:
            emb.set_footer(icon_url=self.context.guild.icon.url,text=self.context.guild.name)
        return await self.context.send(embed=emb)




    def translate_command(self,cog_name,command_name,original_name):
        """
        Find the translated version of the command replies with the definition
        of the command in the invoked language
        """
        try:
            translation = self.lang[cog_name][original_name]
        except KeyError:
            return None
        lang = self.detector.detect(command_name)
        if isinstance(lang.lang,list):
            if lang.lang[1].lower() == "zh-cn":
                return translation['mandarin']
        elif lang.lang.lower() == 'zh-cn':
            return translation['mandarin']
        
        return None

    async def send_command_help(self, command:commands.Command):
        #TODO  ADD LANGUAGE TRANSLATION VERSION FOR WHEN COMMANDS ARE USED
        # Add language specific replies back into the document.
        translated_command = self.translate_command(command.cog_name,self.context.current_argument,command.name)

        if command.name.lower() in self.hidden_func['commands'] and self.context.author.id not in self.context.bot.owner_ids:
            return await self.context.send("You don not have permission to view this command")
        
        if translated_command:
            newline = "\n"
            command_doc = f"{translated_command['doc']}\n{f'{newline}'.join(translated_command['examples'])}"
        else:
            command_doc=command.help
        command_doc = command_doc.replace("{command_prefix}",self.context.prefix)
        command_doc = command_doc.replace("{command_name}",self.context.current_argument)
        aliases=f" {self.context.prefix}".join(command.aliases)
        if command.aliases:
            emb=discord.Embed(title=f"{self.context.prefix}{command.name} **|** {self.context.prefix}{aliases}", description=f"{command_doc}",color=discord.Color.random())
            return await self.context.send(embed=emb)



        emb=discord.Embed(description=f"{self.context.prefix}{command.name}\n{command_doc}",color=discord.Color.random())
        return await self.context.send(embed=emb)


    async def send_cog_help(self,cog):
        cog_help= ""
        if cog.qualified_name == 'Guild':
            prefix_commands = ['add-prefix','remove-prefix','view-prefixes']
            for cmd in self.context.bot.commands:
                if cmd.name in prefix_commands:
                    cog_help+=f"{cmd.name} - {cmd.short_doc}\n"
        if cog.qualified_name == '음악':
            cog = self.context.bot.cogs['Music']
            for cmd in cog.get_commands():
                # NOTE: Can't get command info if disabled
                if not cmd.enabled: continue;
                if cmd.hidden or cmd.name.lower() in self.hidden_func['commands']:
                    if self.context.author.id in self.context.bot.owner_ids:
                        cog_help+=f"{self.lang['Music'][cmd.name]['name']}: - {cmd.short_doc}\n"

                    else:
                        continue
                else:
                    cog_help+=f"{self.lang['Music'][cmd.name]['korean']['name']}: - {cmd.short_doc}\n"

                

            emb = discord.Embed(color=discord.Color.random(),description=cog_help,title="음악")
            if self.context.guild.icon is not None:
                emb.set_thumbnail(url=self.context.guild.icon.url)
                
            return await self.context.send(embed=emb)

        for cmd in cog.get_commands():
            if not cmd.enabled:continue;
            if cmd.hidden:
                if self.context.author.id in self.context.bot.owner_ids:
                    cog_help+= f"{cmd.name} - {cmd.short_doc}\n"
                continue
            else:        
                cog_help+= f"**{cmd.name}** - {cmd.short_doc}\n"

        emb=discord.Embed(title=f"**{cog.qualified_name}**",description=cog_help,color=discord.Color.random())

        if self.context.guild.icon is None:
            emb.set_thumbnail(url="https://cdn.discordapp.com/attachments/671263788862930964/904594760675774464/NA_ICON.png")
        
        else:
            emb.set_thumbnail(url=self.context.guild.icon.url)

        return await self.context.send(embed=emb)




    async def send_group_help(self, group):
        """

        Rewrite the help doc for groups
        """
        commands = list(group.commands)
        group_commands = f"> **{group.short_doc}**\n{self.context.prefix}{group.name} comand-name\nEx: {self.context.prefix}{group.name} {commands[0].name}\nUse {self.context.prefix}help command-name for more information on how to use the command.\n\n\n"


        for cmd in commands:
            if not cmd.enabled or cmd.hidden:
                continue
            group_commands+=f"__{cmd.name}__ - {cmd.short_doc}\n"

        # return await super().send_group_help(group)
        return await self.context.send(group_commands)





class Help(commands.Cog):
    """
    Shows the help command and how to use it 
    """

    def __init__(self, kurusaki):
        self.kurusaki=kurusaki
        self._original_help_command = kurusaki.help_command
        kurusaki.help_command = MyHelpCommand()
        kurusaki.help_command.cog = self



    def cog_unload(self):
        self.bot.help_command= self._original_help_command



    @command()
    async def cogs(self,msg):
        """

        Shows the list of cogs the Kurusaki has
        `Ex:` s.modules
        `Command:` cogs()
        """

        _cogs=""
        cog_dict=self.kurusaki.cogs
        for cog in self.kurusaki.cogs:
            if cog.lower() == 'nsfw' and msg.guild.id == 264445053596991498:
                continue
            
            if cog.lower() == 'events' or cog.lower() == 'economy' or cog.lower() == '음악':
                continue
            else:
                _cogs+=f"`{cog}` - {cog_dict[cog].description}\n"
        

        emb=discord.Embed(description=f"**{self.kurusaki.user.name}'s Command Cogs**\n{_cogs}",color=discord.Color.random())
        return await msg.send(embed=emb)



async def setup(kurusaki):
    await kurusaki.add_cog(Help(kurusaki))