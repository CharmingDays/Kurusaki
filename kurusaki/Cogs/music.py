import asyncio
import json
import math
import random
from typing import Optional
import typing
import discord
from discord.ext.commands.context import Context
import wavelink,os
from motor.motor_asyncio import AsyncIOMotorClient as MotorClient
from discord.ext import commands
from wavelink import Player,Node
from discord.ext import tasks
import spacy


class Music(commands.Cog):
    """
    Play music from Youtube and listen together with people in voice channel
    """
    def __init__(self,bot) -> None:
        self.bot:commands.Bot = bot
        self.players = {}
        self.messages = {}
        self.no_cog_check = ['playlist',' poplaylist','serversongs','nowplaying','np','queue']


    async def load_command_aliases(self):
        command_list = json.loads(open('language.json',encoding='utf-8').read())
        for commandName,languages in command_list['Music'].items():
            command = self.bot.get_command(commandName)
            for language in languages.values():
                command.aliases.append(language['name'])
    
    
    
    async def cog_load(self):
        await self.setup_database()
        server_uri = f"http://{os.getenv('lavalink_server')}:{os.getenv('lavalink_port')}"
        node:Node = Node(uri=server_uri,password=os.getenv("lavalink_password"),identifier='kurusaki')
        await wavelink.Pool.connect(client=self.bot,nodes=[node])
        self.node:Node = wavelink.Pool.get_node('kurusaki')
        print(f"Node: {self.node}")

    async def setup_database(self):
        client = MotorClient(os.getenv("MONGO"))
        database = client['Discord-Bot-Database']
        collection = database['General']
        doc = await collection.find_one("music")
        if doc:
            self.mongoClient = client
            self.mongoCollection = collection
            self.musicDoc = doc


        else:
            self.musicDoc = {}

    # async def cog_command_error(self, ctx: Context, error: commands.CommandError):
    #     if isinstance(error,commands.CommandInvokeError):
    #         return await ctx.send(error.original)



    async def add_guild_volume(self,ctx:Context):
        # Adds the guild to database and set default volume to 50
        self.musicDoc[str(ctx.guild.id)] = {'vol':50}
        filter = {"_id":"music"}
        await self.mongoCollection.update_one(filter,{"$set":{f"{ctx.guild.id}":{"vol":50}}})



    async def cog_before_invoke(self, ctx: Context):
        if not ctx.guild:
            raise commands.CommandInvokeError("Command must be in server.")
        

        if str(ctx.guild.id) not in self.musicDoc:
            # add guild to database
            await self.add_guild_volume(ctx)

        if ctx.command.name.lower() in self.no_cog_check:
            player:Player = self.node.get_player(ctx.guild.id)
            self.players[ctx.guild.id] = player #Cache the player 
            return

        should_join = ctx.command.name.lower() in ['play','loadplaylist','shuffleplaylist','listento']
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandInvokeError("Please join a voice channel first.")

        if not ctx.guild.voice_client:
            if should_join:
                await ctx.author.voice.channel.connect(cls=Player)
                player:Player = self.node.get_player(ctx.guild.id)
                self.players[ctx.guild.id] = player
                return 

        player:Player = self.node.get_player(ctx.guild.id)
        self.players[ctx.guild.id] = player #Cache the player 
        if ctx.author.voice.channel.id != player.channel.id:
            return await ctx.send(f"Please join the same chanel {player.channel.mention} as the bot first.")


    async def should_disconnect(self,guild_id):
        DISCONNECT_AFTER = 120
        await asyncio.sleep(DISCONNECT_AFTER)
        try:
            player:Player = self.players[guild_id]
        except KeyError:
            return
        if not player.current and len(player.queue) == 0:
            # clean up the player and clear queue
            player.cleanup()
            await player.disconnect()
            del self.players[guild_id]
            self.messages.pop(guild_id)



    def convert_to_minutes(self,timeValue):
        # convert the milliseconds from player into minutes
        minutes = (timeValue/1_000)/ 60
        hour = ""
        if minutes >= 60:
            hour+= f"{minutes/60}"
        seconds = int((timeValue/1_000)%60)
        if seconds < 10:
            seconds = f"0{seconds}"
        return f"{math.trunc(minutes)}:{seconds}"



    async def send_interaction(self,ctx:Context,message:str):
        if ctx.interaction != None:
            return await ctx.interaction.response.send_message(message)
        return await ctx.send(message)



    async def send_embed(self,payload:wavelink.TrackStartEventPayload,track:wavelink.Player):
        """
        Sends the embed to channel when a new song is playing
        Embed includes:
            title
            url
            thumbnail
            duration
            volume
            requester
        """
        guild = payload.player.guild
        info = self.messages[guild.id][track.identifier]
        channel = guild.get_channel(info['channel'])
        emb = discord.Embed(title=track.title,url=track.uri,color=discord.Color.random())
        emb.set_footer(text=info['author'],icon_url=info['icon'])
        emb.add_field(name='Duration',value=f"{self.convert_to_minutes(track.length)}")
        emb.add_field(name='Volume',value=payload.player.volume)
        emb.set_thumbnail(url=f"https://img.youtube.com/vi/{track.identifier}/0.jpg")
        if channel.last_message_id == self.messages[guild.id]['last_message']:
            # latest msg = bot msg
            await channel.last_message.edit(embed=emb)
        
        else:
            # new latest message
            message:discord.Message = await channel.send(embed=emb)
            self.messages[message.guild.id]['last_message'] = message.id

    @tasks.loop(minutes=5)
    async def clear_player_cache(self):
        """
        Clear the "cache" from the `self.players` dict that has been idling > `WAIT_TIME`
        """
        WAIT_TIME = 8*60
        for guildId in self.players.copy():
            pass

    @commands.Cog.listener()
    async def on_wavelink_track_start(self,payload:wavelink.TrackStartEventPayload):
        """
        Instructions to run when new track starts
        """
        player: wavelink.Player | None = payload.player
        if not player:
            # TODO handle error when player is not found
            return 
        guildVolume = self.musicDoc[str(payload.player.guild.id)]['vol']
        if player.volume != guildVolume:
            await player.set_volume(guildVolume)
        await self.send_embed(payload,payload.track)



    @commands.Cog.listener()
    async def on_wavelink_track_end(self,payload:wavelink.TrackEndEventPayload):
        player: wavelink.Player | None = payload.player
        if player:
            if player.queue.mode.loop == True:
                return await player.play(payload.track)
            
            if len(player.queue) != 0:
                # paly next song in queue
                next_song = await player.queue.get_wait()
                return await player.play(next_song)
            if not player.current:
                return await self.should_disconnect(player.guild.id)



    @commands.command(name='nowPlaying',aliases=['np','現在播放的音樂'])
    async def now_playing(self,ctx:Context):
        """
        Returns the currently playing song
        {command_prefix}{command_name}
        """
        player:Player = self.players[ctx.guild.id]
        if player and player.is_playing:    
            return await ctx.send(f"[{player.current.title}]({player.current.uri})")
        
        return await ctx.send("No track currently playing")

    @commands.command(aliases=['대기열','隊列'])
    async def queue(self,ctx:Context):
        """
        Check what songs are currently in queue
        {command_prefix}{command_name}
        """
        # TODO add error handler for when message limit > 2000
        # check songs in queue 
        player:Player = self.players[ctx.guild.id]
        if len(player.queue) == 0:
            return await ctx.send("Queue is empty.")
        songs = ""
        for index,song in enumerate(player.queue):
            songs+=f"**{index+1}**: {song.title}\n"
        return await ctx.send(songs)


    async def add_message_info(self,ctx:Context,track:wavelink.Playable):
        """
        Adds last message ID
        track identifier
        author name/icon
        channel
        """
        if ctx.guild.id in self.messages:
            #add new info
            if 'last_message' not in self.messages[ctx.guild.id]:
                self.messages[ctx.guild.id]['last_message'] = None
            self.messages[ctx.guild.id][track.identifier] = {'author':ctx.author.display_name,'icon':ctx.author.display_avatar.url,'channel':ctx.channel.id}
        else:
            #Adds first info
            self.messages[ctx.guild.id] = {'last_message':None,track.identifier:{'author':ctx.author.display_name,'icon':ctx.author.display_avatar.url,'channel':ctx.channel.id}}



    async def match_title(self,title:str,all_tracks:typing.Union[wavelink.Playable,wavelink.Playlist]):
        # iterate through the tracks list and find the closest matching title
        nlp = spacy.load('en_core_web_lg')
        query = nlp(title)
        result = {'accuracy':0,'title':all_tracks[0].title,'index':0}
        for index,track in enumerate(all_tracks):
            target = track.title
            target.replace("-",'')
            vector = query.similarity(nlp(target))
            if vector > result['accuracy']:
                result['accuracy'] = vector
                result['title'] = track.title
                result['index'] = index

        return all_tracks[result['index']]

    async def send_queue_message(self,ctx:Context,player:wavelink.Player,track:wavelink.Playable,embed_title=None):
        if embed_title == None:
            embed_title = track.title
        if ctx.interaction != None:
            # if player.current:
            await player.queue.put_wait(track)
            return await ctx.interaction.response.send_message(f'Added {track.title} to queue.',delete_after=60,ephemeral=True)
        emb = discord.Embed(title="Song Queued",description=f"[{embed_title}]({track.uri})",color=discord.Color.random())
        emb.set_thumbnail(url=f"https://img.youtube.com/vi/{track.identifier}/0.jpg")
        emb.add_field(name='Duration',value=self.convert_to_minutes(track.length))
        emb.set_footer(text=ctx.author.display_name,icon_url=ctx.author.display_avatar.url)
        return await ctx.send(embed=emb)

    @commands.hybrid_command(aliases=['재생','開始'])
    async def play(self,ctx:commands.Context,*,query:str):
        """
        Search and play a song in a voice channel or add song to queue.
        track(required): The title of the song or url to paly from Youtube
        {command_prefix}{command_name} dududu! yaorenmao
        """
        search_result = await wavelink.Playable.search(query)
        player:Player = typing.cast(Player,ctx.voice_client)
        if isinstance(search_result,wavelink.Playlist):
            first_track=search_result.tracks.pop(0)
            await self.add_message_info(ctx,first_track)
            for song in search_result.tracks:
                await player.queue.put_wait(song)
                await self.add_message_info(ctx,song)
            
            await player.play(first_track)
            return await self.send_queue_message(ctx,player,first_track,search_result.name)
        track = await self.match_title(query,search_result)
        await self.add_message_info(ctx,track)

        if player.current:
            # audio playing
            # Queue song
            await player.queue.put_wait(track)
            return await self.send_queue_message(ctx,player,track)
            

        if not player.current:
            # Start first song
            if ctx.interaction != None:
                return await ctx.interaction.response.send_message(f'Now playing {track.title}',ephemeral=True,delete_after=60)
            await self.send_queue_message(ctx,player,track)
            return await player.play(track)
    
    # @play.error
    # async def play_error(self,ctx:Context,error):
    #     # TODO: Find what error is being produced when this error handler is invoked
    #     if isinstance(error.original,wavelink.LavalinkLoadException):
    #         wavelink.TrackExceptionEventPayload
    #         return await self.send_interaction(ctx,error.original.args[0])

    async def load_playlist_songs(self,ctx:Context,player:Player,songs:typing.List[str]):
        for song in songs:
            track:wavelink.Playable = await wavelink.Playable.search(f"https://www.youtube.com/watch?v={song['id']}")
            await self.add_message_info(ctx,track[0])
            await player.queue.put_wait(track[0])
        return await ctx.message.add_reaction('🎶')




    @commands.command(name='shufflePlaylist')
    async def shuffle_playlist(self,ctx:Context):
        songs = self.musicDoc['userPlaylist'][str(ctx.author.id)].copy()
        random.shuffle(songs)
        await ctx.invoke(self.bot.get_command('loadplaylist'),songs=songs)


    
    @shuffle_playlist.before_invoke 
    async def before_shuffle_playlist(self,ctx:Context):
        """
        Check for if user has playlist saved in database
        """
        userPlaylist = self.musicDoc['userPlaylist']
        if str(ctx.author.id) not in userPlaylist:
            raise commands.CommandError("Please add songs to your playlist first.")

    @shuffle_playlist.error
    async def shuffle_playlist_error(self,ctx:Context,error:commands.CommandInvokeError):
        return await ctx.send(error.original)


    @commands.command(name='loadPlaylist',aliases=['加載播放音樂表'])
    async def load_playlist(self,ctx:Context,songs=None):
        """
        Adds the songs in your personal playlist to queue and start it if no song currently playing
        {command_prefix}{command_name}
        """
        if not songs:
            songs = self.musicDoc['userPlaylist'][str(ctx.author.id)]
        if str(ctx.author.id) not in self.musicDoc['userPlaylist']:
            return await ctx.send("You don't have any songs saved.")
        
        player:Player = self.players[ctx.guild.id]
        if player.current:
            return await self.load_playlist_songs(ctx,player,songs)
        first_song  = songs.pop(0)
        first_track = await wavelink.Playable.search(f"https://www.youtube.com/watch?v={first_song['id']}")
        await self.add_message_info(ctx,first_track[0])
        await player.play(first_track[0])
        return await self.load_playlist_songs(ctx,player,songs)


    @commands.command(name='listenTo',aliases=['聼'])
    async def listen_to(self,ctx:Context,guildId:int,trackPosition:int=0):
        """
        Listen along to the songs another server is playing
        guildId(required): The serverId that you're trying to listen along with
        trackPosition(optional): Whether to start track from beginning (`0`) or play at the same track position (`1`) as the other server.
        {command_prefix}{command_name} serverId
        {command_prefix}{command_name} 823742837412 1
        """
        if trackPosition not in [0,1]:
            return await ctx.send("Please use `1` to play at same track position or `0` to start from beginning")
        targetPlayer:Player = self.players[guildId]
        if trackPosition == 1:
            trackPosition = targetPlayer.last_position
        player:Player = self.players[ctx.guild.id]
        songId = targetPlayer.current.identifier
        track:wavelink.Playable = await wavelink.YouTubeTrack.search(f"https://www.youtube.com/watch?v={songId}")
        await self.add_message_info(ctx,track[0])
        await player.play(track[0],start=trackPosition)


    @commands.command(name='serverSongs',aliases=['목록','服務器歌曲'])
    async def guild_songs(self,ctx:Context):
        """
        View songs playing in other servers
        To listen along, use command {command_prefix}listenTo serverId
        {command_prefix}{command_name}
        """
        # checks what songs other servers are listening to
        players = self.node.players
        if not players:
            return await ctx.send("No songs playing")
        all_songs = ""
        for player in players.values():
            all_songs+=f"**{player.guild.name} ({player.guild.id})** - `{player.current.title}`\n"
        return await ctx.send(all_songs)


    @commands.command(aliases=['停止'])
    async def stop(self,ctx:Context):
        """
        Stops the audio and clear all song in queue
        {command_prefix}{command_name}
        """
        player:Player = self.players[ctx.guild.id]
        if player.current:
            player.queue.clear()
            await player.stop()
            return await ctx.message.add_reaction('✅')
        return await ctx.send("Audio already stopped.")


    @commands.command(name='dcme')
    async def disconnect_me(self,ctx:Context):
        """
        Disconnects bot from voice channel and the user if the user the user is alone after bot leaves
        """
        player:Player = self.players[ctx.guild.id]
        del self.players[ctx.guild.id]
        if player.current:
            player.queue.clear()
            await player.stop()
        player.cleanup()
        await player.disconnect()
        voice_members = [member for member in ctx.author.voice.channel.members if not member.bot]
        if len(voice_members) == 1:
            await voice_members[0].move_to(channel=None)
        return await ctx.message.add_reaction('✅')


    @commands.command(aliases=['dc','leave','끝','切斷'])
    async def disconnect(self,ctx:Context):
        """ 
        Disconnects the bot from the voice channel and clears queued songs.
        {command_prefix}{command_name}
        """
        player:Player = self.players[ctx.guild.id]
        del self.players[ctx.guild.id]
        if player.current:
            player.queue.clear()
            await player.stop()

        player.cleanup()
        await player.disconnect()
        return await ctx.message.add_reaction('✅')


    @commands.command(name='popQueue',aliases=['삭제','把歌從隊列移除'])
    async def pop_queue(self,ctx:Context,position:int):
        """
        Remove song from queue by position.
        {command_prefix}{command_name} position
        position(required): The position(index) of the song in list
        {command_prefix}{command_name} 3
        """
        player:Player = self.players[ctx.guild.id]
        previous_tracks = [track for track in player.queue]
        removed_track = previous_tracks.pop(position-1)
        player.queue.clear()
        for track in previous_tracks:
            await player.queue.put_wait(track)
        
        return await ctx.send(f"Removed **{removed_track.title}** from queue")


    @commands.command(name='popPlaylist',aliases=['把播放音樂表移除'])
    async def pop_playlist(self,ctx:Context,position:int):
        """
        Removed a song saved from your playlist with given index
        {command_prefix}{command_name} position
        position(required): The position of the song on your playlist to remove
        {command_prefix}{command_name} 3 
        """
        if str(ctx.author.id) not in self.musicDoc['userPlaylist']:
            return await ctx.send("You do not have songs in your playlist")
        
        removed = self.musicDoc['userPlaylist'][str(ctx.author.id)].pop(position-1)
        await self.mongoCollection.update_one({"_id":"music"},{"$pull":{f"userPlaylist.{ctx.author.id}":removed}})
        return await ctx.send(f"Removed song **{removed['title']}** from your playlist.")

    
    @commands.command()
    async def command(self,ctx,*,playlist_url):
        """
        loads the songs from a youtube playlist into your discord bot playlist
        """


    @commands.command(aliases=['내목록','我的音樂表'])
    async def playlist(self,ctx:Context):
        """
        View your saved songs.
        {command_prefix}{command_name}
        """
        if str(ctx.author.id) not in self.musicDoc['userPlaylist']:
            return await ctx.send("You don't have any saved songs")
        
        songs =""
        for index,song in enumerate(self.musicDoc['userPlaylist'][str(ctx.author.id)]):
            songs+=f"**{index+1}**: {song['title']}\n"
        return await ctx.send(songs)



    @commands.command(name='saveSong',aliases=['저장','保存歌曲'])
    async def save_song(self,ctx:Context):
        """
        Save a song to your playlist that the bot is currently playing
        {command_prefix}{command_name}
        """
        player:Player = self.players[ctx.guild.id]
        filter = {"_id":"music"}
        if not player.current:
            return await ctx.send("No song currently playing to save.")

        if str(ctx.author.id) in self.musicDoc['userPlaylist']:
            song_ids = [song['id'] for song in self.musicDoc['userPlaylist'][str(ctx.author.id)]]
            if player.current.identifier in song_ids:
                return await ctx.send(f"**{player.current.title}** already saved.")
        
        
            else:
                self.musicDoc['userPlaylist'][str(ctx.author.id)].append({"title":player.current.title,"id":player.current.identifier})
                await self.mongoCollection.update_one(filter,{"$push":{f"userPlaylist.{ctx.author.id}":{"title":player.current.title,"id":player.current.identifier}}})
        else:
            self.musicDoc['userPlaylist'][str(ctx.author.id)] = [{"title":player.current.title,"id":player.current.identifier}]
            await self.mongoCollection.update_many(filter,{"$set":{f"userPlaylist.{ctx.author.id}":[{"title":player.current.title,"id":player.current.identifier}]}})
        
        return await ctx.send(f"Saved **{player.current.title}** to your playlist")


    @commands.command(aliases=['시간','尋找'])
    async def seek(self,ctx:Context,position:int):
        """
        Jump to a specific in the current audio playing. Value must be in seconds.
        {command_prefix}{command_name} track_time
        track(required): The time to skip to in seconds
        {command_prefix}{command_name} 120
        """
        position*=1000
        player:Player = self.players[ctx.guild.id]
        if position >= player.current.length:
            return await ctx.send("Position exceeds or equals to song duration")
        
        return await player.seek(position)

    @commands.command(aliases=['스킵','跳過'])
    async def skip(self,ctx:Context,position:Optional[int]):
        """
        Skip the current song the bot is playing or to a specific position in queue.
        {command_prefix}{command_name} position
        position(optional): The position to skip to in queue
        {command_prefix}{command_name}
        {command_prefix}{command_name} 3
        """
        # TODO Skipping to wrong queue or `shuffleplaylist` adding wrong queue positions
        # skip to the next song or to a specific position in queue
        player:Player = self.players[ctx.guild.id]
        if len(player.queue) ==0:
            return await ctx.send("No songs in queue to skip to.")
        if position:
            if position > len(player.queue):
                return await ctx.send(f"Position exceeds queue count of {len(player.queue)}")
            else:
                songs = [song for song in player.queue]
                player.queue.clear()
                await player.queue.put_wait(songs.pop(position-1))
                for song in songs:
                    await player.queue.put_wait(song)
                await player.stop()
        await player.stop()
        return await ctx.message.add_reaction('⏭')


    @commands.command(aliases=['일시정지','暫停'])
    async def pause(self,ctx:Context):
        """
        Pause the music
        {command_prefix}{command_name}
        """
        player:Player = self.players[ctx.guild.id]

        if not player.current:
            return await ctx.send("No audio currently playing")
        
        if player.paused:
            return await ctx.send("Already paused")
        
        await player.pause(True)
        return await ctx.message.add_reaction('⏸')


    @commands.command(aliases=['재개','繼續'])
    async def resume(self,ctx:Context):
        """
        Resume the paused audio 
        {command_prefix}{command_name}
        """
        player:Player = self.players[ctx.guild.id]
        if not player.current:
            return await ctx.send('No audio in track')
        
        if not player.paused:
            return await ctx.send("Audio already playing.")

        await player.pause(False)
        return await ctx.message.add_reaction('▶️')


    @commands.command(aliases=['반복','重複'])
    async def repeat(self,ctx:Context):
        """
        Set song loop on/off.
        {command_prefix}{command_name}
        """
        player:Player = self.players[ctx.guild.id]
        if not player:
            return await ctx.send("No audio playing.")
        if player.queue.mode.loop == True:
            player.queue.mode.loop = False
            return await ctx.send("Stopped loop")
        player.queue.mode.loop = True
        return await ctx.send("Looping current song.")


    @commands.command(aliases=['vol','볼륨','音量'])
    async def volume(self,ctx:Context,_volume:typing.Optional[int]):
        """
        Set the volume of the bot.
        {command_prefix}{command_name} volume
        volume(optional): The volume for the music playing. If not provide, return current volume
        {command_prefix}{command_name} 200
        NOTE: max is 100, and makes it inaudible.
        """
        # NOTE: Rate limit volume updating later when more servers added
        player:Player = self.players[ctx.guild.id]
        if not _volume:
            return await ctx.send(f'Volume: **{player.volume}%**')
        if _volume >200:
            _volume = 200
            await ctx.send("Set volume to 200 because it can't exceed 200.")
        await player.set_volume(_volume)
        self.musicDoc[str(ctx.guild.id)]['vol'] = _volume
        await self.mongoCollection.update_one({"_id":"music"},{"$set":{f"{ctx.guild.id}.vol":_volume}})
        return await ctx.send(f"Set volume to {_volume}")



from dotenv import load_dotenv
load_dotenv()

async def setup(bot):
    await bot.add_cog(Music(bot))
