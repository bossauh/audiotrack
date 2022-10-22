import os
import sys

sys.path.append(os.path.join(os.getcwd(), ".."))

from audiotrack.input import InputTrack
from audiotrack.output import OutputTrack

input_track = InputTrack("Microphone", blocksize=512, samplerate=16000, chunk_size=512)
output_track = OutputTrack("Output", blocksize=512, samplerate=16000, vol=1.5)
added = []

while True:
    try:
        nd_data = input_track.read()
        if nd_data is not None:
            output_track.queue.put(nd_data)
    except KeyboardInterrupt:
        break
