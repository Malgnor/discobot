from disco.bot import Plugin
from disco.bot.command import CommandError
from disco.voice.player import Player
from disco.voice.playable import YoutubeDLInput, BufferedOpusEncoderPlayable
from disco.voice.client import VoiceException
from six.moves import queue
from random import shuffle

def on_start_play(guild_member):
    def _on_start_play(item):
        nickname = 'Playing: ' + (item.info['alt_title'] or item.info['title'])
        if len(nickname) > 32:
            nickname = nickname[:29]+'...'
        guild_member.set_nickname(nickname)
    return _on_start_play

def on_stop_play(player, playlist):
    def _on_stop_play(item):
        if playlist and not playlist.empty():
            player.queue.put(playlist.get().pipe(BufferedOpusEncoderPlayable))
    return _on_stop_play

def on_disconnect(guild_member):
    def _on_disconnect():
        guild_member.set_nickname(None)
    return _on_disconnect

def remove_angular_brackets(url):
    if url[0] is '<' and url[-1] is '>':
        return url[1:-1]
    return url

class MusicPlugin(Plugin):
    def load(self, ctx):
        super(MusicPlugin, self).load(ctx)
        self.guilds = {}
        self.playlist = {}

    # @Plugin.listen('VoiceStateUpdate')
    # def on_voice_update(self, event):
        # pass

    @Plugin.command('join')
    def on_join(self, event):
        if event.guild.id in self.guilds:
            return event.msg.reply("I'm already playing music here.")

        state = event.guild.get_member(event.author).get_voice_state()
        if not state:
            return event.msg.reply('You must be connected to voice to use that command.')

        try:
            client = state.channel.connect()
        except VoiceException as e:
            return event.msg.reply('Failed to connect to voice: `{}`'.format(e))

        player = Player(client)
        self.guilds[event.guild.id] = player
        self.playlist[event.guild.id] = queue.Queue()
        member = event.guild.get_member(self.state.me.id)
        player.events.on(player.Events.START_PLAY, on_start_play(member))
        player.events.on(player.Events.STOP_PLAY, on_stop_play(player, self.playlist[event.guild.id]))
        player.events.on(player.Events.DISCONNECT, on_disconnect(member))
        player.complete.wait()
        if event.guild.id in self.guilds:
            del self.guilds[event.guild.id]
        if event.guild.id in self.playlist:
            del self.playlist[event.guild.id]

    def get_player(self, guild_id):
        if guild_id not in self.guilds:
            raise CommandError("I'm not currently playing music here.")
        return self.guilds.get(guild_id)

    def get_playlist(self, guild_id):
        if guild_id not in self.playlist:
            raise CommandError("I'm not currently playing music here.")
        return self.playlist.get(guild_id)

    @Plugin.command('leave')
    def on_leave(self, event):
        player = self.get_player(event.guild.id)
        player.disconnect()
        if event.guild.id in self.guilds:
            del self.guilds[event.guild.id]
        if event.guild.id in self.playlist:
            del self.playlist[event.guild.id]

    @Plugin.command('play', '<url:str>')
    def on_play(self, event, url):
        item = YoutubeDLInput(remove_angular_brackets(url)).pipe(BufferedOpusEncoderPlayable)
        self.get_player(event.guild.id).queue.put(item)

    @Plugin.command('playl', '<url:str>')
    def on_playlist(self, event, url):
        items = list(YoutubeDLInput.many(remove_angular_brackets(url)))
        self.get_player(event.guild.id).queue.put(items[0].pipe(BufferedOpusEncoderPlayable))
        self.get_player(event.guild.id).queue.put(items[1].pipe(BufferedOpusEncoderPlayable))
        for item in items[2:]:
            self.get_playlist(event.guild.id).put(item)

    @Plugin.command('playlr', '<url:str>')
    def on_playlistrandom(self, event, url):
        items = list(YoutubeDLInput.many(remove_angular_brackets(url)))
        shuffle(items)
        self.get_player(event.guild.id).queue.put(items[0].pipe(BufferedOpusEncoderPlayable))
        self.get_player(event.guild.id).queue.put(items[1].pipe(BufferedOpusEncoderPlayable))
        for item in items[2:]:
            self.get_playlist(event.guild.id).put(item)

    @Plugin.command('pause')
    def on_pause(self, event):
        self.get_player(event.guild.id).pause()

    @Plugin.command('resume')
    def on_resume(self, event):
        self.get_player(event.guild.id).resume()

    @Plugin.command('skip')
    def on_skip(self, event):
        self.get_player(event.guild.id).skip()

    @Plugin.command('link')
    def on_link(self, event):
        if self.get_player(event.guild.id).now_playing:
            info = self.get_player(event.guild.id).now_playing.info
            return event.msg.reply('{}'.format(info['webpage_url']))
