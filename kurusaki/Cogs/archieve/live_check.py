import discord
import asyncio
from discord.ext import commands
from discord.utils import get
from discord.ext import tasks, commands
from youtube_dl import YoutubeDL

class live_check(commands.Cog):
    def __init__(self, Kurusaki):
        self.live_channels = []

        self.Kurusaki = Kurusaki

        
    @commands.command()
    async def live_update(self, ctx):
        channel = await ctx.guild.create_text_channel(name='Hololive_live_notice')
        self.live_channels.append(channel.id)
        print("live_update ",self.live_channels)
        self.get_live.start()

    @tasks.loop(seconds= 10)
    async def get_live(self):
        
        youtube_dl_opts = {
            '--socket-timeout': 5
        }
        vtubers ={"Kurusaki": False, "calli": False,"kiara": False, "ina": False, "watson": False, "iris": False}
        while True:
            links = ["https://www.youtube.com/channel/UCoSrY_IQQVpmIRZ9Xf-y93g/live",   #Kurusaki
            "https://www.youtube.com/channel/UCL_qhgtOy0dy1Agp8vkySQg/live",                 #calli
            "https://www.youtube.com/channel/UCHsx4Hqa-1ORjQTh9TYDhww/live",                 #kiara
            "https://www.youtube.com/channel/UCMwGHR0BTZuLsmjY_NT5Pwg/live",                 #ina
            "https://www.youtube.com/channel/UCyl1z3jo3XHR1riLFKG5UAg/live",                 #watson
            "https://www.youtube.com/channel/UC8rcEBzJSleTkf_-agPM20g/live"]                 #iris


            #get the information about the video including id and live(bool)
            for x in links:
                with YoutubeDL(youtube_dl_opts) as ydl:
                    info_dict = ydl.extract_info(x, download= False)
                    live = info_dict.get('is_live', None)
                    video_id = info_dict.get('id', None)
                
                """
                check if the vtuber is streaming or not. 
                If she is, send message to 'notice' channel and change the status to True in vtubers dictionary
                """
                index = links.index(x)
                index_val = list(vtubers.values())[index]

                print(live)
                if index_val == False and live == True:
                    print("https://www.youtube.com/watch?v=" + video_id)
                    print("get_live",self.live_channels)
                    for x in self.live_channels :
                        print(x)
                        channel = self.Kurusaki.get_channel(x)
                        await channel.send("https://www.youtube.com/watch?v=" +video_id)
                    index_val = True
                elif index_val == True and live == True:
                    print("already on")
                elif index_val == True and live == False:
                    print("not live")
                    index_val = False

            await asyncio.sleep(60)

    @get_live.before_loop
    async def before_get_live(self):
        await self.Kurusaki.wait_until_ready()

async def setup(Kurusaki):
    await Kurusaki.add_cog(live_check(Kurusaki))
