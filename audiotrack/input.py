import logging
import threading
import time
from typing import Callable, Optional, Union

import numpy as np
import sounddevice as sd

from .config import config

logger = logging.getLogger(__name__)


class InputTrack:
    """
    An `InputTrack` is a type of track that accepts input devices such as microphones.
    The data coming from the input device can then be modified in real time by a `InputTrack`.
    An example of a data modification is changing the volume, adding effects, etc.

    The modified data can then be read using the `InputTrack.read()` method or it can be casted into a `OutputTrack` which essentially just plays the modified data in real time.

    Attributes
    ----------
    `name` : str
        The name of this track. It doesn't have to conform to any guidelines.
    `callback` : Optional[Callable]
        A user supplied function that takes in three arguments, the first argument is the current
        input track, the second argument is the ndarray that is coming from the input device.
        The third argument is the overflow status. The function can then modify this ndarray
        and return it back. Defaults to None.
        There should always be a returned ndarray.
    `samplerate` : Optional[int]
        The samplerate of this InputTrack. Passed onto `sd.InputStream`. Defaults to None. Which is
        `config.default_input_track_samplerate`
    `blocksize` : Optional[int]
        The blocksize of this InputTrack. Passed onto `sd.InputStream`. Defaults to None.
    `device` : Optional[Union[int, str]]
        The device to use for this InputTrack. Passed onto `sd.InputStream`. Defaults to None.
    `dtype` : str
        The dtype to be fed into `sd.InputStream`. Defaults to `"float32"`
    `chunk_size` : int
        The size of each chunk returned from `.read()`. Defaults to 512.
    `stream_parameters` : Optional[dict]
        Extra parameters to be passed onto `sd.InputStream`. Defaults to None.
    """

    def __init__(
        self,
        name: str,
        callback: Optional[Callable] = None,
        samplerate: Optional[int] = None,
        blocksize: Optional[int] = None,
        device: Optional[Union[int, str]] = None,
        dtype: str = "float32",
        chunk_size: int = 512,
        stream_parameters: Optional[dict] = None,
    ) -> None:

        # Attributes
        self.name = name
        self.callback = callback
        self.samplerate = samplerate or config.default_input_track_samplerate
        self.blocksize = blocksize
        self.device = device
        self.dtype = dtype
        self.chunk_size = chunk_size
        self.stream_parameters = stream_parameters or {}
        self.stream = None

        #### Internal attributes
        self.__data = None
        self.__buffer = []

        #### State related attributes
        self.overflow = False
        self.stopped = True
        self._stop_signal = False

        self.start()

    def start(self) -> None:

        """
        Start the InputTrack. This makes it so that you can finally call `.read()` and it would
        start returning data. This function won't return until the stream is actually started.
        """

        logger.debug(f"Starting input track '{self.name}'")
        threading.Thread(target=self.__start__, daemon=True).start()

        while self.stopped:
            time.sleep(0.001)
        logger.info(f"Input track '{self.name}' started.")

    def stop(self) -> None:
        """
        Stop the InputTrack. This makes it so that you can no longer call `.read()`. This function
        won't return until the stream is actually stopped.
        """

        logger.debug(f"Stopping input track '{self.name}'")

        self._stop_signal = True
        while not self.stopped:
            time.sleep(0.001)

        logger.info(f"Input track '{self.name}' stopped.")

    def read(self, check_size: int = 1024) -> Optional[np.ndarray]:
        """
        Read the data coming from the InputStream.

        Returns
        -------
        `np.ndarray` :
            Audio data with shape of (frames (or size of chunks), channels).
        `None` :
            If the data that's supposed to be returned is the same as the last few returned data. When calling .read() constantly (which you most likely would), you should always check if the value is None.
        """

        data = self.__data
        if data is None:
            return

        if self.callback:
            data = self.callback(self, data, self.overflow)

        data = np.resize(data, (self.chunk_size, self.stream.channels))
        if any((data == x).all() for x in self.__buffer):
            return

        self.__buffer.append(data)
        if len(self.__buffer) > check_size:
            self.__buffer.pop(0)

        return data

    def __start__(self) -> None:
        with sd.InputStream(
            samplerate=self.samplerate,
            blocksize=self.blocksize,
            device=self.device,
            dtype=self.dtype,
            **self.stream_parameters,
        ) as f:
            self.stopped = False
            self.stream = f

            while not self._stop_signal:
                try:
                    data, overflow = f.read(self.chunk_size)
                except sd.PortAudioError:
                    break

                self.__data = data
                self.overflow = overflow

                time.sleep(0.001)

        self.stopped = True
        self.stream = None
        self.__data = None
        self._stop_signal = False
