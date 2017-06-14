from random import shuffle
from disco.bot import Plugin
from disco.bot.command import CommandError
from disco.voice.player import Player
from disco.voice.playable import YoutubeDLInput, BufferedOpusEncoderPlayable, UnbufferedOpusEncoderPlayable
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
        self.autopause = False
        self.autovolume = True
        self.volume = 0.1
        self.ducking_volume = 0.1
        self.anyonespeaking = False

        self.events.on(self.Events.START_PLAY, self.on_start_play)
        self.events.on(self.Events.STOP_PLAY, self.on_stop_play)
        self.events.on(self.Events.EMPTY_QUEUE, self.on_empty_queue)
        self.events.on(self.Events.DISCONNECT, self.on_disconnect)
        self.client.packets.on(VoiceOPCode.SPEAKING, self.on_speaking)

    def on_start_play(self, item):
        nickname = '🎵 ' + (item.info.get('alt_title')
                           or item.info.get('title', ''))
        if len(nickname) > 32:
            nickname = nickname[:29] + '...'
        self.guild_member.set_nickname(nickname)
        self.update_volume()

    def on_stop_play(self, _):
        if not self.playlist.empty():
            self.queue.put(self.playlist.get().pipe(
                UnbufferedOpusEncoderPlayable))

    def on_empty_queue(self):
        if not self.playlist.empty():
            self.queue.put(self.playlist.get().pipe(
                UnbufferedOpusEncoderPlayable))
        else:
            self.guild_member.set_nickname(self.nick)

    def on_disconnect(self):
        self.guild_member.set_nickname(self.nick)

    def on_speaking(self, data):
        if (not self.autopause) and (not self.autovolume):
            return

        if not self.guild.get_member(data['user_id']).get_voice_state().channel is self.client.channel:
            return

        self.speaking[data['user_id']] = data['speaking']

        self.anyonespeaking = any(self.speaking.values())

        if self.autovolume:
            self.update_volume()
        elif self.autopause:
            if self.anyonespeaking:
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
            self.resume()
        else:
            self.autovolume = False

    @property
    def autovolume(self):
        return self.__autovolume

    @autovolume.setter
    def autovolume(self, value):
        self.__autovolume = value
        if value:
            self.autopause = False

    @property
    def volume(self):
        return self.__base_volume

    @volume.setter
    def volume(self, value):
        self.__base_volume = value
        self.update_volume()

    @property
    def ducking_volume(self):
        return self.__ducking_volume

    @ducking_volume.setter
    def ducking_volume(self, value):
        self.__ducking_volume = value
        self.update_volume()

    def update_volume(self):
        if isinstance(self.now_playing, UnbufferedOpusEncoderPlayable):
            if self.autovolume and self.anyonespeaking:
                self.now_playing.volume = self.__base_volume * self.ducking_volume
            else:
                self.now_playing.volume = self.__base_volume


class MusicPlugin(Plugin):
    def load(self, ctx):
        super(MusicPlugin, self).load(ctx)
        self.guilds = {}

    @Plugin.listen('VoiceStateUpdate')
    def on_voice_update(self, event):
        if event.state.user == self.state.me:
            try:
                player = self.get_player(event.guild.id)
                if event.state.deaf and player.now_playing:
                    player.skip()
            except CommandError:
                pass

    @Plugin.command('join')
    def on_join(self, event):
        if event.guild.id in self.guilds:
            return event.msg.reply("Já estou tocando música aqui.")

        state = event.guild.get_member(event.author).get_voice_state()
        if not state:
            return event.msg.reply('Você precisa estar conectado em um canal de voz para usar este comando.')

        try:
            client = state.channel.connect()
        except VoiceException as e:
            return event.msg.reply('Falha ao conectar no canal de voz: `{}`'.format(e))

        self.guilds[event.guild.id] = MusicPlayer(
            client, event.guild.get_member(self.state.me.id), event.guild)

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
        item = YoutubeDLInput(remove_angular_brackets(
            url)).pipe(UnbufferedOpusEncoderPlayable)
        self.get_player(event.guild.id).queue.put(item)

    @Plugin.command('playl', '<url:str>')
    def on_playlist(self, event, url):
        items = list(YoutubeDLInput.many(remove_angular_brackets(url)))
        self.get_player(event.guild.id).queue.put(
            items[0].pipe(UnbufferedOpusEncoderPlayable))
        self.get_player(event.guild.id).queue.put(
            items[1].pipe(UnbufferedOpusEncoderPlayable))
        for item in items[2:]:
            self.get_player(event.guild.id).playlist.put(item)

    @Plugin.command('playlr', '<url:str>')
    def on_playlistrandom(self, event, url):
        items = list(YoutubeDLInput.many(remove_angular_brackets(url)))
        shuffle(items)
        self.get_player(event.guild.id).queue.put(
            items[0].pipe(UnbufferedOpusEncoderPlayable))
        self.get_player(event.guild.id).queue.put(
            items[1].pipe(UnbufferedOpusEncoderPlayable))
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
        self.get_player(event.guild.id).autopause = not self.get_player(
            event.guild.id).autopause
        return event.msg.reply('Autopause foi {}.'.format('ativado' if self.get_player(event.guild.id).autopause else 'desativado'))

    @Plugin.command('autovolume')
    def on_autovolume(self, event):
        self.get_player(event.guild.id).autovolume = not self.get_player(
            event.guild.id).autovolume
        return event.msg.reply('Autovolume foi {}.'.format('ativado' if self.get_player(event.guild.id).autovolume else 'desativado'))

    @Plugin.command('volume', '[vol:float]')
    def on_volume(self, event, vol=None):
        player = self.get_player(event.guild.id)
        if vol:
            player.volume = vol
        else:
            return event.msg.reply('Volume atual: {}'.format(player.volume))

    @Plugin.command('duckingvolume', '[vol:float]')
    def on_ducking_volume(self, event, vol=None):
        player = self.get_player(event.guild.id)
        if vol:
            player.ducking_volume = vol
        else:
            return event.msg.reply('Atenuação atual: {}'.format(player.ducking_volume))
