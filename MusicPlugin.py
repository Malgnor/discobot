import json

import gevent
from disco.bot import Plugin
from disco.bot.command import CommandError
from disco.voice.client import VoiceException
from disco.voice.packets import VoiceOPCode
from disco.voice.playable import UnbufferedOpusEncoderPlayable, YoutubeDLInput
from disco.voice.player import Player
from disco.voice.queue import PlayableQueue
from flask import abort, jsonify, redirect, request, url_for

from Utils import ServerSentEvent, remove_angular_brackets


def gen_player_data(player):
    data = {}
    data['paused'] = True if player.paused else False
    data['volume'] = player.volume
    data['duckingVolume'] = player.ducking_volume
    data['autopause'] = player.autopause
    data['autovolume'] = player.autovolume
    data['queue'] = len(player.queue)
    data['items'] = len(player.items)
    data['playlist'] = [{'id': value.info['id'], 'title':value.info['title'],
                         'duration':value.info['duration'], 'webpageUrl':value.info['webpage_url']} for value in player.queue]
    data['curItem'] = None
    if player.now_playing:
        data['curItem'] = {
            'id': player.now_playing.info['id'],
            'duration': player.now_playing.info['duration'],
            'webpageUrl': player.now_playing.info['webpage_url'],
            'title': player.now_playing.info['title'],
            'thumbnail': player.now_playing.info['thumbnail'],
            'fps': player.now_playing.sampling_rate * player.now_playing.sample_size / player.now_playing.frame_size,
            'frame': player.tell_or_seek() / player.now_playing.frame_size
        }

    return data


class CircularQueue(PlayableQueue):
    def get(self):
        # pylint: disable=W0212
        item = self._get()
        if item.source and item.source._buffer and item.source._buffer.seekable():
            item.source._buffer.seek(0)
        self.append(item)
        return item

    def remove(self, index):
        if len(self._data) > index:
            return self._data.pop(index)
        return None

    def prepend(self, item):
        self._data.insert(0, item)

        if self._event:
            self._event.set()
            self._event = None

    def contains(self, item, func):
        for i in self._data:
            if func(i, item):
                return True
        return False


class MusicPlayer(Player):
    def __init__(self, client, guild_member, guild):
        super(MusicPlayer, self).__init__(client, CircularQueue())
        self.guild_member = guild_member
        self.guild = guild
        self.nick = guild_member.nick
        self.speaking = {}
        self.__autopause = self.autopause = False
        self.__autovolume = self.autovolume = True
        self.__base_volume = self.volume = 0.1
        self.__ducking_volume = self.ducking_volume = 0.1
        self.__clear = False
        self.anyonespeaking = False
        self.items = PlayableQueue()
        self.listeners = []
        self.send_stats = False

        gevent.spawn(self.__add_items)
        gevent.spawn(self.__keep_alive)

        self.events.on(self.Events.START_PLAY, self.on_start_play)
        self.events.on(self.Events.EMPTY_QUEUE,
                       self.on_disconnect_or_empty_queue)
        self.events.on(self.Events.DISCONNECT,
                       self.on_disconnect_or_empty_queue)
        self.events.on(self.Events.FIRST_FRAME, self.on_first_frame)
        self.client.packets.on(VoiceOPCode.SPEAKING, self.on_speaking)

    def on_start_play(self, item):
        nickname = '🎵 ' + (item.info.get('alt_title')
                           or item.info.get('title', ''))
        if len(nickname) > 32:
            nickname = nickname[:29] + '...'
        self.guild_member.set_nickname(nickname)
        self.update_volume()
        self.send_stats = True

    def on_disconnect_or_empty_queue(self):
        self.guild_member.set_nickname(self.nick)

    def on_first_frame(self):
        self.add_event(event='firstframe', data=json.dumps({'frame': 0}))

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
        else:
            self.update_volume()

    @property
    def volume(self):
        return self.__base_volume

    @volume.setter
    def volume(self, value):
        self.__base_volume = value
        self.update_volume()
        self.add_event(event='volumeupdate', data=json.dumps({'vol': value}))

    @property
    def ducking_volume(self):
        return self.__ducking_volume

    @ducking_volume.setter
    def ducking_volume(self, value):
        self.__ducking_volume = value
        self.update_volume()
        self.add_event(event='volumeupdate', data=json.dumps({'dvol': value}))

    def update_volume(self):
        if isinstance(self.now_playing, UnbufferedOpusEncoderPlayable):
            if self.autovolume and self.anyonespeaking:
                self.now_playing.volume = self.__base_volume * self.ducking_volume
            else:
                self.now_playing.volume = self.__base_volume

    def __add_items(self):
        while True:
            try:
                item = self.items.get()
                if item.info and not self.queue.contains(item, lambda i1, i2: i1.info['id'] == i2.info['id']):
                    item = item.pipe(UnbufferedOpusEncoderPlayable)
                    self.queue.append(item)
                    self.add_event(event='playlistadd', data=json.dumps(
                        {'id': item.info['id'], 'duration': item.info['duration'], 'webpageUrl': item.info['webpage_url'], 'title': item.info['title'],
                         'thumbnail': item.info['thumbnail'], 'fps': item.sampling_rate * item.sample_size / item.frame_size, 'frame': 0}))
            except Exception:  # pylint: disable=W0703
                pass
            if self.__clear:
                self.__clear = False
                self.queue.clear()
                self.send_stats = True
                self.add_event(event='playlistupdate', data=json.dumps([{'id': value.info['id'], 'title':value.info['title'],
                                                                         'duration':value.info['duration'], 'webpageUrl':value.info['webpage_url']} for value in self.queue]))

    def clear(self):
        self.items.clear()
        self.queue.clear()
        self.__clear = True
        self.send_stats = True
        self.add_event(event='playlistupdate', data=json.dumps([{'id': value.info['id'], 'title':value.info['title'],
                                                                 'duration':value.info['duration'], 'webpageUrl':value.info['webpage_url']} for value in self.queue]))

    def tell_or_seek(self, offset=None):
        # pylint: disable=W0212
        if self.now_playing and self.now_playing.source and self.now_playing.source._buffer and self.now_playing.source._buffer.seekable():
            if offset is None:
                return self.now_playing.source._buffer.tell()
            self.now_playing.source._buffer.seek(offset)
            self.send_stats = True
            return offset
        return -1

    def __add_event(self, **kwargs):
        for listener in self.listeners:
            listener.put(ServerSentEvent(**kwargs))

    def add_event(self, **kwargs):
        gevent.spawn(self.__add_event, **kwargs)

    def __keep_alive(self):
        count = 0
        while True:
            gevent.sleep(1)
            count += 1
            if self.send_stats or count == 5:
                self.send_stats = False
                count = 0
                self.add_event(event='stats', data=json.dumps(
                    gen_player_data(self)))
                continue
            self.add_event(comment='keepalive')


class MusicPlugin(Plugin):
    def load(self, ctx):
        super(MusicPlugin, self).load(ctx)
        self.guilds = {}  # pylint: disable=W0201

    @Plugin.listen('VoiceStateUpdate')
    def on_voice_update(self, event):
        if event.state.user == self.state.me:
            try:
                player = self.get_player(event.guild.id)
                if event.state.deaf and player.now_playing:
                    player.skip()
                    player.send_stats = True
            except CommandError:
                pass

    @Plugin.command('join', description='Faz o bot se conectar ao seu canal de voz.')
    def on_join(self, event):
        if event.guild.id in self.guilds:
            return event.msg.reply('Já estou tocando música aqui.')

        state = event.guild.get_member(event.author).get_voice_state()
        if not state:
            return event.msg.reply('Você precisa estar conectado em um canal de voz para usar este comando.')

        try:
            client = state.channel.connect()
        except VoiceException as exception:
            return event.msg.reply('Falha ao conectar no canal de voz: `{}`'.format(exception))

        self.guilds[event.guild.id] = MusicPlayer(
            client, event.guild.get_member(self.state.me.id), event.guild)

        if self.bot.config.http_enabled:
            with self.bot.http.app_context():
                event.msg.reply(
                    url_for('on_player_route', guild=event.guild.id))

        self.guilds[event.guild.id].complete.wait()

        if event.guild.id in self.guilds:
            del self.guilds[event.guild.id]

    def get_player(self, guild_id):
        if guild_id not in self.guilds:
            raise CommandError('Não estou tocando música aqui.')
        return self.guilds.get(guild_id)

    @Plugin.command('leave', description='Faz o bot se desconectar do canal de voz.')
    def on_leave(self, event):
        player = self.get_player(event.guild.id)
        player.disconnect()
        if event.guild.id in self.guilds:
            del self.guilds[event.guild.id]

    @Plugin.command('play', '<url:str>', description='Adiciona um item na playlist.')
    def on_play(self, event, url):
        self.get_player(event.guild.id).items.append(
            YoutubeDLInput(remove_angular_brackets(url)))

    @Plugin.command('playlist', '<url:str>', description='Adiciona vários items na playlist.')
    def on_playlist(self, event, url):
        for item in YoutubeDLInput.many(remove_angular_brackets(url)):
            self.get_player(event.guild.id).items.append(item)

    @Plugin.command('shuffle', description='Embaralha a playlist.')
    def on_shuffle(self, event):
        self.get_player(event.guild.id).queue.shuffle()
        self.get_player(event.guild.id).add_event(event='playlistupdate', data=json.dumps([{'id': value.info['id'], 'title':value.info['title'],
                                                                                            'duration':value.info['duration'], 'webpageUrl':value.info['webpage_url']} for value in self.get_player(event.guild.id).queue]))

    @Plugin.command('pause', description='Pausa o player.')
    def on_pause(self, event):
        self.get_player(event.guild.id).pause()
        self.get_player(event.guild.id).send_stats = True

    @Plugin.command('resume', description='Despausa o player.')
    def on_resume(self, event):
        self.get_player(event.guild.id).resume()
        self.get_player(event.guild.id).send_stats = True

    @Plugin.command('skip', description='Pula o item atual.')
    def on_skip(self, event):
        if self.get_player(event.guild.id).now_playing:
            self.get_player(event.guild.id).skip()
            self.get_player(event.guild.id).send_stats = True

    @Plugin.command('link', description='Mostra o link do item atual.')
    def on_link(self, event):
        if self.get_player(event.guild.id).now_playing:
            info = self.get_player(event.guild.id).now_playing.info
            return event.msg.reply('{}'.format(info.get('webpage_url', 'Não tem. :(')))
        return event.msg.reply('Não estou tocando no momento.')

    @Plugin.command('autopause', description='Ativa/desativa o autopause.')
    def on_autopause(self, event):
        self.get_player(event.guild.id).autopause = not self.get_player(
            event.guild.id).autopause
        self.get_player(event.guild.id).send_stats = True
        return event.msg.reply('Autopause foi {}.'.format('ativado' if self.get_player(event.guild.id).autopause else 'desativado'))

    @Plugin.command('autovolume', description='Ativa/desativa o autovolume.')
    def on_autovolume(self, event):
        self.get_player(event.guild.id).autovolume = not self.get_player(
            event.guild.id).autovolume
        self.get_player(event.guild.id).send_stats = True
        return event.msg.reply('Autovolume foi {}.'.format('ativado' if self.get_player(event.guild.id).autovolume else 'desativado'))

    @Plugin.command('volume', '[vol:float]', description='Altera o volume.')
    def on_volume(self, event, vol=None):
        player = self.get_player(event.guild.id)
        if vol:
            player.volume = vol
            player.send_stats = True
        else:
            return event.msg.reply('Volume atual: {}'.format(player.volume))

    @Plugin.command('duckingvolume', '[vol:float]', description='Altera a atenuação do autovolume.')
    def on_ducking_volume(self, event, vol=None):
        player = self.get_player(event.guild.id)
        if vol:
            player.ducking_volume = vol
            player.send_stats = True
        else:
            return event.msg.reply('Atenuação atual: {}'.format(player.ducking_volume))

    @Plugin.route('/player/')
    @Plugin.route('/player/<int:guild>/')
    def on_player_route(self, guild=0):
        from flask import render_template

        try:
            channelid = int(request.args.get('channel', 0))
        except ValueError as exception:
            return jsonify(error='Falha ao converter valor: {}'.format(exception))

        if channelid:
            try:
                channel = self.state.channels[channelid]
            except KeyError as exception:
                return jsonify(error='Canal não encontrado.\nId: {}'.format(channelid))
            if channel.is_guild and channel.is_voice:
                if channel.guild_id not in self.guilds:
                    try:
                        client = channel.connect()
                    except VoiceException as exception:
                        return jsonify(error='Falha ao conectar no canal de voz: `{}`'.format(exception))

                    self.guilds[channel.guild_id] = MusicPlayer(
                        client, channel.guild.get_member(self.state.me.id), channel.guild)

                return redirect(url_for('on_player_route', guild=channel.guild_id))
            else:
                return jsonify(error='Canal precisa ser um canal do tipo voz e pertencer a uma guild.\nCanal: {}\nGuild: {}\nVoz: {}'.format(channel, channel.is_guild, channel.is_voice))

        if 'notangular' in request.args or self.guilds.get(guild) is None:
            return render_template('player.html', player=self.guilds.get(guild))

        return render_template('player.angular.html')

    @Plugin.route('/player/join/')
    def on_player_join_route(self):
        from flask import render_template

        info = {
            'players': [],
            'guilds': []
        }

        for guild in self.state.guilds.values():
            if guild.id in self.guilds:
                info['players'].append((guild.name, guild.id))
                continue

            channels = []
            for channel in guild.channels.values():
                if not channel.is_voice:
                    continue

                channels.append((channel.name, channel.id))

            if channels:
                info['guilds'].append((guild.name, guild.id, channels))

        return render_template('player_list.html', info=info)

    @Plugin.route('/player/<int:guild>/add', methods=['POST'])
    def on_player_add_route(self, guild):

        if guild not in self.guilds:
            abort(400)

        url = request.form['url']
        message = {}

        if 'playlist' in request.form:
            items = list(YoutubeDLInput.many(url))
            for item in items:
                self.get_player(guild).items.append(item)
            message['message'] = '{} foram adicionados na playlist.'.format(
                len(items))
            message['type'] = 'success'
            self.get_player(guild).send_stats = True
        else:
            item = YoutubeDLInput(url)

            self.get_player(guild).items.append(item)
            message['message'] = '"{}" foi adicionado na playlist.'.format(
                item.info['title'])
            message['type'] = 'success'
            self.get_player(guild).send_stats = True

        return jsonify(action='add', data={'url': url}, message=message)

    @Plugin.route('/player/<int:guild>/<string:action>')
    def on_player_queue_action_route(self, guild, action):

        if guild not in self.guilds:
            abort(400)

        player = self.get_player(guild)
        data = {}
        message = {}

        if action == 'shuffle':
            player.queue.shuffle()
            message['message'] = 'Playlist foi embaralhada.'
            message['type'] = 'info'
            player.add_event(event='playlistupdate', data=json.dumps([{'id': value.info['id'], 'title':value.info['title'],
                                                                       'duration':value.info['duration'], 'webpageUrl':value.info['webpage_url']} for value in player.queue]))
        elif action == 'clear':
            player.clear()
            message['message'] = 'Playlist foi esvaziada.'
            message['type'] = 'info'
        elif action == 'play' or action == 'resume':
            player.resume()
            data['paused'] = True if player.paused else False
            message['message'] = 'O player foi despausado.'
            message['type'] = 'info'
        elif action == 'pause':
            player.pause()
            data['paused'] = True if player.paused else False
            message['message'] = 'O player foi pausado.'
            message['type'] = 'info'
        elif action == 'skip':
            if player.now_playing:
                player.skip()
            player.resume()
            data['paused'] = True if player.paused else False
        elif action == 'leave':
            player.disconnect()
            del self.guilds[guild]
            return redirect(url_for('on_player_route'))
        elif action == 'duck':
            player.autovolume = True
            data['autovolume'] = player.autovolume
        elif action == 'autopause':
            player.autopause = True
            data['autopause'] = player.autopause
        elif action == 'noduckorpause':
            player.autopause = False
            player.autovolume = False
            data['autovolume'] = player.autovolume
            data['autopause'] = player.autopause
        else:
            abort(400)

        player.send_stats = True

        return jsonify(action=action, data=data, message=message)

    @Plugin.route('/player/<int:guild>/<string:action>/<value>')
    def on_player_action_route(self, guild, action, value):

        if guild not in self.guilds:
            abort(400)

        player = self.get_player(guild)
        data = {}
        message = {}

        if action == 'remove':
            index = int(value)
            data['index'] = index
            item = player.queue.remove(index)
            message['message'] = '{} foi removido da playlist.'.format(
                item.info['title'])
            message['type'] = 'info'
            player.add_event(event='playlistupdate', data=json.dumps([{'id': value.info['id'], 'title':value.info['title'],
                                                                       'duration':value.info['duration'], 'webpageUrl':value.info['webpage_url']} for value in player.queue]))
        elif action == 'play':
            index = int(value)
            data['index'] = index
            item = player.queue.remove(index)
            if item:
                player.queue.prepend(item)
                if player.now_playing:
                    player.skip()
                player.resume()
                message['message'] = '{} está tocando agora.'.format(
                    item.info['title'])
                message['type'] = 'info'
                player.add_event(event='playlistupdate', data=json.dumps([{'id': value.info['id'], 'title':value.info['title'],
                                                                           'duration':value.info['duration'], 'webpageUrl':value.info['webpage_url']} for value in player.queue]))
        elif action == 'vol':
            volume = float(value)
            player.volume = volume
            data['volume'] = volume
        elif action == 'dvol':
            volume = float(value)
            player.ducking_volume = volume
            data['duckingVolume'] = volume
        elif action == 'seek':
            if player.now_playing:
                seconds = int(value)
                player.tell_or_seek(
                    seconds * player.now_playing.sampling_rate * player.now_playing.sample_size)
                data['seconds'] = seconds
        else:
            abort(400)

        player.send_stats = True

        return jsonify(action=action, data=data, message=message)

    @Plugin.route("/player/<int:guild>/events/")
    def on_subscribe_events(self, guild):
        from flask import Response

        if guild not in self.guilds:
            abort(400)

        player = self.get_player(guild)

        data = gen_player_data(player)

        def gen():
            queue = gevent.queue.Queue()
            queue.put(ServerSentEvent(
                event='handshake', data=json.dumps(data)))
            player.listeners.append(queue)
            try:
                while True:
                    result = queue.get()
                    yield result.encode()
            except GeneratorExit:
                player.listeners.remove(queue)

        return Response(gen(), mimetype="text/event-stream")
