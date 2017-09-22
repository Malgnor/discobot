import array
import os

from disco.voice.playable import (AbstractOpus, BasePlayable, BufferedIO,
                                  OpusEncoder, YoutubeDLInput)
from disco.voice.queue import PlayableQueue
from gevent.fileobject import FileObjectThread


class YoutubeDLFInput(YoutubeDLInput):
    def read(self, sz):
        if sz is 0:
            if not os.path.isfile(os.path.join('data', self.info['id'])):
                f_obj = open(os.path.join('data', self.info['id']), 'wb')
                file = FileObjectThread(f_obj, 'wb')
                super(YoutubeDLFInput, self).read(0)
                file.write(self._buffer.read())
                file.close()
                self.close()
            return b''

        if not self._buffer:

            if os.path.isfile(os.path.join('data', self.info['id'])):
                with open(os.path.join('data', self.info['id']), 'rb') as file:
                    self._buffer = BufferedIO(file.read())
            else:
                f_obj = open(os.path.join('data', self.info['id']), 'wb')
                file = FileObjectThread(f_obj, 'wb')
                super(YoutubeDLFInput, self).read(0)
                file.write(self._buffer.read())
                file.close()
                self._buffer.seekable() and self._buffer.seek(0)

        return self._buffer.read(sz)

    def close(self):
        if self._buffer:
            self._buffer.close()
            self._buffer = None


class UnbufferedOpusEncoderPlayable(BasePlayable, OpusEncoder, AbstractOpus):
    def __init__(self, source, *args, **kwargs):
        self.source = source
        if hasattr(source, 'info'):
            self.info = source.info
        self.volume = 1.0

        library_path = kwargs.pop('library_path', None)

        AbstractOpus.__init__(self, *args, **kwargs)

        OpusEncoder.__init__(self, self.sampling_rate,
                             self.channels, library_path=library_path)

        self.source.read(0)

    def next_frame(self):
        if self.source:
            raw = self.source.read(self.frame_size)
            if len(raw) < self.frame_size:
                self.source.close()
                return None

            if self.volume == 1.0:
                return self.encode(raw, self.samples_per_frame)

            buffer = array.array('h', raw)
            for pos, byte in enumerate(buffer):
                buffer[pos] = int(min(32767, max(-32767, byte * self.volume)))
            return self.encode(buffer.tobytes(), self.samples_per_frame)
        return None


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
