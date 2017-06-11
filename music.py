from random import shuffle
from disco.bot import Plugin
from disco.bot.command import CommandError
from disco.voice.player import Player
from disco.voice.playable import YoutubeDLInput, BufferedOpusEncoderPlayable
from disco.voice.client import VoiceException
from disco.voice.packets import VoiceOPCode
from six.moves import queue


def remove_angular_brackets(url):
    if url[0] is '<' and url[-1] is '>':
        return url[1:-1]
    return url

class MusicPlayer(Player):
    def __init__(self, client, guild_member, guild):
        super(MusicPlayer, self).__init__(client)
        self.guild_member = guild_member
        self.guild = guild
        self.nick = guild_member.nick
        self.playlist = queue.Queue()
        self.speaking = {}
        self.deaf = False
        self.autopause = True

        self.events.on(self.Events.START_PLAY, self.on_start_play)
        self.events.on(self.Events.STOP_PLAY, self.on_stop_play)
        self.events.on(self.Events.DISCONNECT, self.on_disconnect)
        self.client.packets.on(VoiceOPCode.SPEAKING, self.on_speaking)

    def on_start_play(self, item):
        nickname = '🎵 ' + (item.info.get('alt_title') or item.info.get('title', ''))
        if len(nickname) > 32:
            nickname = nickname[:29]+'...'
        self.guild_member.set_nickname(nickname)

    def on_stop_play(self, item):
        if self.playlist and not self.playlist.empty():
            self.queue.put(self.playlist.get().pipe(BufferedOpusEncoderPlayable))

    def on_disconnect(self):
        self.guild_member.set_nickname(self.nick)

    def on_speaking(self, data):
        if not self.autopause:
            return
        if not self.guild.get_member(data['user_id']).get_voice_state().channel is self.client.channel:
            return
        self.speaking[data['user_id']] = data['speaking']
        if any(self.speaking.values()):
            self.pause()
        else:
            self.resume()

    @property
    def autopause(self):
        return self.__autopause

    @autopause.setter
    def autopause(self, value):
        self.__autopause = value
        if not value:
            self.resume

class MusicPlugin(Plugin):
    def load(self, ctx):
        super(MusicPlugin, self).load(ctx)
        self.guilds = {}

    @Plugin.listen('VoiceStateUpdate')
    def on_voice_update(self, event):
        if event.state.user == self.state.me:
            try:
                player = self.get_player(event.guild.id)
                if not player.deaf is event.state.deaf:
                    player.deaf = event.state.deaf
                    if player.now_playing:
                        player.skip()
            except CommandError as e:
                pass

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

        self.guilds[event.guild.id] = MusicPlayer(client, event.guild.get_member(self.state.me.id), event.guild)

        self.guilds[event.guild.id].complete.wait()

        if event.guild.id in self.guilds:
            del self.guilds[event.guild.id]

    def get_player(self, guild_id):
        if guild_id not in self.guilds:
            raise CommandError("I'm not currently playing music here.")
        return self.guilds.get(guild_id)

    @Plugin.command('leave')
    def on_leave(self, event):
        player = self.get_player(event.guild.id)
        player.disconnect()
        if event.guild.id in self.guilds:
            del self.guilds[event.guild.id]

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
            self.get_player(event.guild.id).playlist.put(item)

    @Plugin.command('playlr', '<url:str>')
    def on_playlistrandom(self, event, url):
        items = list(YoutubeDLInput.many(remove_angular_brackets(url)))
        shuffle(items)
        self.get_player(event.guild.id).queue.put(items[0].pipe(BufferedOpusEncoderPlayable))
        self.get_player(event.guild.id).queue.put(items[1].pipe(BufferedOpusEncoderPlayable))
        for item in items[2:]:
            self.get_player(event.guild.id).playlist.put(item)

    @Plugin.command('pause')
    def on_pause(self, event):
        self.get_player(event.guild.id).pause()

    @Plugin.command('resume')
    def on_resume(self, event):
        self.get_player(event.guild.id).resume()

    @Plugin.command('skip')
    def on_skip(self, event):
        if self.get_player(event.guild.id).now_playing:
            self.get_player(event.guild.id).skip()

    @Plugin.command('link')
    def on_link(self, event):
        if self.get_player(event.guild.id).now_playing:
            info = self.get_player(event.guild.id).now_playing.info
            return event.msg.reply('{}'.format(info.get('webpage_url', 'Não tem. :(')))
        return event.msg.reply('Não estou tocando no momento.')

    @Plugin.command('autopause')
    def on_autopause(self, event):
        self.get_player(event.guild.id).autopause = not self.get_player(event.guild.id).autopause
        return event.msg.reply('Autopause foi {}.'.format('ativado' if self.get_player(event.guild.id).autopause else 'desativado'))