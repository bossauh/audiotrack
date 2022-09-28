import dataclasses
import logging
import os
import pathlib
from typing import Callable, Optional, Tuple, Union

import ffmpy
import soundfile as sf

from .config import config

logger = logging.getLogger()


@dataclasses.dataclass
class AudioFile:

    """
    Represents a audio file that can be played by a output track.
    The reason why this is a class is so that we can have some unique
    configurations for each audio file.

    Attributes
    ----------
    `path` : str
        The path to the audio file.
    `repeat` : Union[int, Callable]
        How many times should the audio file be looped. Defaults to 0 which means play it once.
        This attribute can also be a callable that returns the actual integer value.
    `vol` : float
        The volume to use when playing this audio file. Defaults to 1.0 which is 100%.
        The volume can obviously still be overwritten if the volume has been manually changed
        in the middle of playing the audio file.
    `on_end` : Optional[Callable]
        A user supplied callback function that gets called every time the audio file ends. Defaults to None.
        The function must accept two arguments, the first one is the `AudioFile` instance and
        the second one is the remaining counter for `repeat`. If it's 0 then that means
        that's the last time the audio file will ever be played.
    """

    path: str
    repeat: Union[int, Callable] = 0
    vol: float = 1.0
    on_end: Optional[Callable] = None

    def get_repeat(self) -> int:
        repeat = self.repeat
        if not isinstance(repeat, int):
            repeat = repeat()

        return repeat

    def validate(self) -> Tuple[bool, Optional[int]]:
        """
        Check if the audio file can be read by soundfile.

        Returns
        -------
        `Tuple[bool, int]` :
            The first value indicates if it can indeed be read. The second value
            is just the samplerate of this audio file if reading is successful, else it
            would be a `None` value.
        """

        try:
            _, rate = sf.read(self.path)
            return (True, rate)
        except RuntimeError:
            return (False, None)

    def convert(self) -> None:
        """
        Convert this audio file into a format that can be read by soundfile.
        Once converted, the `path` attribute of this `AudioFile` instance will be
        replaced by the new file.

        Keep in mind this does need ffmpeg, a `ffmpy.FFExecutableNotFoundError` will
        be raised if ffmpeg is not found.
        """

        logger.debug(
            f"Converting {self.path} into a .{config.valid_audio_format} format."
        )

        # Create the conversions path directory if it doesn't exist yet
        pathlib.Path(config.conversion_path).mkdir(parents=True, exist_ok=True)
        out = os.path.splitext(self.path)[0] + f".{config.valid_audio_format}"
        out = os.path.basename(out)
        out = os.path.join(config.conversion_path, out)

        ff = ffmpy.FFmpeg(
            inputs={self.path: None},
            outputs={out: None},
            global_options=["-loglevel", "quiet", "-y"],
        )
        ff.run()
        logger.debug(f"{self.path} -> {out}")
        self.path = out

    def convert_if_invalid(self) -> None:
        """
        If the format of this audio file is invalid, (cannot be read by soundfile) then
        try to convert it to a valid format.
        """

        valid, _ = self.validate()
        if not valid:
            self.convert()
