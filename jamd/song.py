# Copyright 2013 Stefan Hajnoczi <stefanha@gmail.com>

import json
import types

__all__ = 'Song'

class Song(object):
    '''A song description including tempo, chords, and audio files'''

    def __init__(self, tracks, bpm=None, bpi=None):
        self.tracks = tracks
        self.bpm = bpm
        self.bpi = bpi

    @staticmethod
    def validateSongDict(data):
        tracks = data.get('tracks', {})
        if not isinstance(tracks, dict):
            raise ValueError('expected tracks dictionary')
        for name, intervals in list(tracks.items()):
            if not isinstance(intervals, list):
                raise ValueError('expected track intervals list for "%s"' % name)
            for i in intervals:
                if not isinstance(i, (str, type(None))):
                    raise ValueError('expected track interval string or None')

        if 'bpm' in data:
            if not isinstance(data['bpm'], int):
                raise ValueError('expected bpm integer')
        if 'bpi' in data:
            if not isinstance(data['bpi'], int):
                raise ValueError('expected bpi integer')

    @staticmethod
    def loadJSON(data):
        data = json.loads(data)
        Song.validateSongDict(data)
        return Song(data.get('tracks', {}),
                    data.get('bpm', None),
                    data.get('bpi', None))
