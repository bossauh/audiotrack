"""
Contains the main `OutputTrack` class. An `OutputTrack` is what's responsible for opening a constant `sd.OutputStream` in the background. 
We can then play audio by putting some ndarray data into the output track's queue.
"""

import logging
import math
import queue
import threading
import time
from typing import Callable, Optional, Union

import numpy as np
import sounddevice as sd
import soundfile as sf

from .audiofile import AudioFile
from .config import config
from .exceptions import *

logger = logging.getLogger(__name__)


class OutputTrack:
    """
    An `OutputTrack` is a type of track that lets you play audio by putting ndarray data
    into the output track's queue. Multiple output tracks can overlap each other and play
    audio on top of one another but each output track is only capable of playing one audio.

    Notes
    -----
    - The shape of the ndarray being fed into a output track must be the same shape as
    the output track's `shape` attribute.

    Attributes
    ----------
    `name` : str
        The name of this track. It doesn't have to conform to any guidelines.
    `callback` : Callable
        A user supplied function that takes in two arguments, the first argument is the current
        output track and the second argument is the ndarray that is currently about to be played.
        The function can then modify this ndarray and return it back in order to play the modified ndarray.
        There should always be a returned ndarray.
    `queue_size` : int
        The maximum number of frames to put in the queue. Defaults to `20`. Generally you don't
        have to change this.
    `samplerate` : Optional[int]
        The initial samplerate of this OutputTrack. Defaults to None which is `config.default_output_track_samplerate`.
        Note that the samplerate can be changed by calling `self.update_samplerate(rate: int)`
    `blocksize` : int
        The blocksize to be fed into `sd.OutputStream`. Defaults to `None` which means to calculate it
        based on the sample rate of the track.
    `device` : Optional[Union[int, str]]
        The device to use for this OutputTrack. Passed onto `sd.OutputTrack`. Defaults to None.
    `dtype` : str
        The dtype to be fed into `sd.OutputStream`. Defaults to `"float32"`
    `stream_parameters` : Optional[dict]
        Extra parameters to be passed onto `sd.OutputStream`. Defaults to None.

    Audio Attributes
    ----------------
    `vol` : float
        The initial volume of the track. Defaults to 1 which is 100%. You can go higher than 1 but it
        will start sounding like absolute dog shit.
    """

    def __init__(
        self,
        name: str,
        callback: Optional[Callable] = None,
        queue_size: int = 20,
        samplerate: Optional[int] = None,
        blocksize: Optional[int] = None,
        device: Optional[Union[int, str]] = None,
        dtype: str = "float32",
        stream_parameters: Optional[dict] = None,
        vol: float = 1.0,
    ) -> None:

        # Attributes
        self.name = name
        self.callback = callback
        self.samplerate = samplerate or config.default_output_track_samplerate
        self.blocksize = blocksize
        self.device = device
        self.dtype = dtype
        self.stream_parameters = stream_parameters or {}

        #### Internal attributes
        self.shape = None
        self.queue = queue.Queue(queue_size)

        #### State related attributes
        self.occupied = False
        self.stopped = False
        self._stop_signal = False
        self.paused = False

        #### Audio effects related attributes
        self.vol = vol
        self.__previous_vol = self.vol

        #### Audio file attributes
        self.audio_file: Optional[AudioFile] = None

        self.start()

    def resume(self, smooth: bool = False) -> None:
        """
        Resume this output track.

        Parameters
        ----------
        `smooth` : bool
            Whether to fade into a resumed state rather than instantly resuming. Defaults to `False`.
        """

        self.paused = False
        if smooth:
            self.set_volume(self.__previous_vol)

    def pause(self, smooth: bool = False) -> None:
        """
        Pause this output track.

        Parameters
        ----------
        `smooth` : bool
            Whether to fade into a paused state rather than instantly pausing. Defaults to `False`.
        """

        if smooth:
            self.set_volume(0)
        self.paused = True

    def set_volume(self, vol: float, smoothness: float = 0.005) -> None:
        """
        Change the volume of the track with some smoothness involved.
        You can also change the volume by simply doing `self.vol = x`.
        Please keep in mind that this is a blocking function and might take some
        time to complete depending on the `smoothness` value.

        Parameters
        ----------
        `vol` : float
            The new volume to switch to.
        `smoothness` : float
            How smooth the change will be. Defaults to 0.005.
            The higher this is, the smoother it is.
        """

        self.__previous_vol = self.vol
        inc = 0.01
        while abs(self.vol - vol) > 0.01:
            if vol > self.vol:
                self.vol += inc
            elif vol < self.vol:
                self.vol -= inc

            time.sleep(smoothness)

    def start(self) -> None:
        """
        Start the output track. An output stream is always started when you
        initialize one, so there's really no point in calling this manually.
        This method is a blocking method as it has to wait for the track to actually
        be fully started before returning.
        """

        logger.debug(f"Starting output track '{self.name}'")
        threading.Thread(target=self.__start, daemon=True).start()

        while self.shape is None:
            time.sleep(0.01)
        logger.info(f"Output track '{self.name}' started.")

    def stop(self) -> None:
        """
        Stop the output track. This is a blocking function and this has to wait for
        the track to actually be stopped before returning.
        """

        logger.debug(f"Stopping output track '{self.name}'")

        self._stop_signal = True
        while not self.stopped:
            time.sleep(0.001)

        self.audio_file = None
        with self.queue.mutex:
            self.queue.queue.clear()

        logger.info(f"Output track '{self.name}' stopped.")

    def update_samplerate(self, rate: int) -> None:
        """
        Update the samplerate of this output track. When updating, the audio track
        will be restarted as well in order for the changes to apply.

        Parameters
        ----------
        `rate` : int
            The brand new samplerate.
        """

        if rate == self.samplerate:
            return

        logger.debug(
            f"Updating samplerate of output track '{self.name}' from {self.samplerate} to {rate}."
        )
        self.stop()
        self.samplerate = rate
        self.start()
        logger.info(
            f"Samplerate of output track '{self.name}' has been updated to {rate}."
        )

    def play_audio_file(
        self,
        audio_file: AudioFile,
        blocking: bool = False,
        load_in_memory: bool = False,
        play_immediately: bool = True,
    ) -> None:

        """
        Play an audio file. This methods expects An `AudioFile` object rather than a path to the
        audio file itself.

        Parameters
        ----------
        `audio_file` : AudioFile
            The `AudioFile` object containing the path to the audio file and other information.
        `blocking` : bool
            Whether this function should block or not.
        `load_in_memory` : bool
            Whether to load this audio file into the system memory. Defaults to False.
            You can use this for smaller files which would yield a better performance.
        `play_immediately` : bool
            Whether to play the audio file immediately. Defaults to True. If this is false,
            all it would do is call `self.pause()` before it starts putting in ndarray in the
            queue.
        """

        # Make sure the audio file's format is supported.
        # If the format is not supported, it will try to convert it into a supported format.
        valid, rate = audio_file.validate()
        if not valid:
            rate = audio_file.convert()

        def get_samplerate(i: int = 0):

            """
            Validate if the audio file is valid, if it's not, attempt to convert it
            into a valid format. Once/if the audio file is valid, return the samplerate.

            Raises
            ------
            `UnsupportedFormat` :
                Raised if the audio file has already been converted but for god knows why, it's
                still invalid.
            """

            valid, rate = audio_file.validate()
            if not valid:
                if i == 1:
                    # Raise a unsupported format error if it has been already converted
                    # but is still considered invalid.
                    raise UnsupportedFormat(audio_file)

                audio_file.convert()
                return get_samplerate(i + 1)
            return rate

        rate = get_samplerate()

        if rate != self.samplerate:
            self.update_samplerate(rate)
        else:
            if self.audio_file is not None:
                # Restart it to stop the currently playing audio file if there is any.
                self.stop()
                self.start()

        def get_nds():

            """
            A function that returns a new nds generator every time it's called.
            This is stored in a function because we want to be able to essentially
            reset the ndarray generator.
            """

            return sf.blocks(
                audio_file.path,
                blocksize=self.blocksize,
                always_2d=True,
                fill_value=np.array([0]),
                dtype=self.dtype,
            )

        def player():
            """
            The player function that is responsible for putting the nd
            arrays to this track's queue. This is stored in a function so that
            we can have the option of running it in the background using the threading
            module.
            """

            i = 0
            self.audio_file = audio_file
            self.set_volume(audio_file.vol)

            if not play_immediately and not self.paused:
                self.pause(smooth=False)

            if play_immediately and self.paused:
                self.resume(smooth=False)

            while True:
                try:
                    chunks = get_nds()
                    if load_in_memory:
                        chunks = list(chunks)

                    # Start putting the ndarray data into the queue
                    # This is basically what plays the audio file
                    for ndarray in chunks:
                        if self.audio_file is None:
                            if audio_file.on_end:
                                audio_file.on_end(audio_file, 0)
                            return
                        self.queue.put(ndarray)

                    repeat_left = audio_file.get_repeat() - i

                    if audio_file.on_end:
                        audio_file.on_end(audio_file, repeat_left)

                    if repeat_left == 0:
                        break

                    i += 1
                except KeyboardInterrupt:
                    if audio_file.on_end:
                        audio_file.on_end(audio_file, 0)
                    break

            self.set_volume(self.__previous_vol)

        if blocking:
            return player()
        threading.Thread(target=player, daemon=True).start()

    def __apply_fx(self, data: np.ndarray) -> np.ndarray:
        """
        Applies some basic audio effects to the provided `data`. The provided `data` will
        not be modified but rather a copy will be made and that copy with the modifications
        will be returned.

        There's really only one audio effect right now and that is the volume.
        In the future if my ass finally stops being lazy and works on this even more, then
        maybe more audio effects will be added.
        """

        # Apply the volume effect
        data = np.multiply(
            data,
            pow(2, (math.sqrt(math.sqrt(math.sqrt(self.vol))) * 192 - 192) / 6),
            casting="unsafe",
        )
        return data

    def __start(self) -> None:

        self.stopped = False
        self.occupied = False
        self.shape = None

        with sd.OutputStream(
            samplerate=self.samplerate,
            blocksize=self.blocksize,
            callback=self.__callback__,
            device=self.device,
            dtype=self.dtype,
            **self.stream_parameters,
        ):
            while not self._stop_signal:
                try:
                    time.sleep(0.001)
                except KeyboardInterrupt:
                    self.stop()

        self.stopped = True
        self._stop_signal = False

    # pylint: disable=unused-argument
    def __callback__(self, outdata, frames, time_, status) -> None:
        self.shape = outdata.shape
        self.blocksize = self.shape[0]

        if not self.paused:
            try:
                data = self.queue.get(block=False)
                self.occupied = True
            except queue.Empty:
                self.occupied = False
                data = None

            if self.occupied:
                if self.callback is not None:
                    data = self.callback(self, data)

                if data is not None:
                    outdata[:] = self.__apply_fx(data)
        else:
            outdata[:] = 0
