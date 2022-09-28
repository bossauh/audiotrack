import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .audiofile import AudioFile


class AudioTrackException(Exception):
    """
    Base exception for all audiotrack related exceptions.
    """


class UnsupportedFormat(AudioTrackException):
    """
    Raised if you're trying to load a audio file with a unsupported format
    into a output track.
    """

    def __init__(self, audio_file: "AudioFile") -> None:
        super().__init__()
        self.audio_file = audio_file
        self.format = os.path.splitext(audio_file.path)[-1][1:]
