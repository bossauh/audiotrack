"""
This file demonstrates the major capabilities of audiotrack.
In this demo, i've split the song "It gets funkier by Vulfpeck" into parts,
each part is its own instrument isolated from the rest of the track.

We're then going to play all of them at once and it will sound as if the full song is being
played. The demo will also test out other capabilities.

Note: You need to `pip install coloredlogs` for this to work.
"""


import logging
import os
import sys
import threading
import time

import coloredlogs

sys.path.append(os.path.join(os.getcwd(), ".."))

from audiotrack.audiofile import AudioFile
from audiotrack.config import config
from audiotrack.output import OutputTrack

coloredlogs.install(level="DEBUG")

config.conversion_path = os.path.join(os.getcwd(), "demo_files", "conversion_path")
MP3S = os.path.join(os.getcwd(), "demo_files", "mp3s")

# Instrument Tracks
bass = OutputTrack("Bass")
drums = OutputTrack("Drums")
other = OutputTrack("Other")
piano = OutputTrack("Piano")
vocals = OutputTrack("Vocals")

# Audio files for each instrument
# We're also going to convert each instrument into a valid format if it's invalid.
# play_audio_file already does this but since we want the tracks to be in sync,
# we're going to do it before we even play all of them together.
bass_file = AudioFile(os.path.join(MP3S, "bass.mp3"))
drums_file = AudioFile(os.path.join(MP3S, "drums.mp3"))
other_file = AudioFile(os.path.join(MP3S, "other.mp3"))
piano_file = AudioFile(os.path.join(MP3S, "piano.mp3"))
vocals_file = AudioFile(os.path.join(MP3S, "vocals.mp3"))

bass_file.convert_if_invalid()
drums_file.convert_if_invalid()
other_file.convert_if_invalid()
piano_file.convert_if_invalid()
vocals_file.convert_if_invalid()

# Then finally play all of them at the same time.
# Even tho `play_audio_file` is non-blocking when playing, it still
# takes some time to return so we're using threading
functions = [
    (bass.play_audio_file, (bass_file,)),
    (drums.play_audio_file, (drums_file,)),
    (other.play_audio_file, (other_file,)),
    (piano.play_audio_file, (piano_file,)),
    (vocals.play_audio_file, (vocals_file,)),
]
for f in functions:
    threading.Thread(target=f[0], args=f[1]).start()

time.sleep(7)

# Showcase the smooth volume function
bass.set_volume(0)
time.sleep(2)
bass.set_volume(1)
time.sleep(2)

# Showcase muting tracks. Muting is essentially just setting the volume to 0 instantly.
bass.vol = 0
other.vol = 0
piano.vol = 0
vocals.vol = 0
time.sleep(5)
drums.vol = 0
bass.vol = 1
other.vol = 1
piano.vol = 1
vocals.col = 1
time.sleep(5)
drums.set_volume(1, smoothness=0.05)
time.sleep(5)

# Pause the drums, then play again, this would make it off beat on purpose
drums.pause()
time.sleep(2)
drums.resume()

# After 10 seconds, stop it gets funkier
time.sleep(5)
bass.set_volume(0, smoothness=0.01)
drums.set_volume(0, smoothness=0.01)
other.set_volume(0, smoothness=0.01)
piano.set_volume(0, smoothness=0.01)
vocals.set_volume(0, smoothness=0.01)
bass.stop()
drums.stop()
other.stop()
piano.stop()
vocals.stop()

# Showcase the repeating audio files
sfx = OutputTrack("SFX")
sfx_file = AudioFile(os.path.join(MP3S, "vine_boom.mp3"), repeat=1)


def on_end(audio_file, repeat_left):
    logging.info(f"Repeat left: {repeat_left}")
    audio_file.repeat += 1


sfx_file.on_end = on_end


sfx.play_audio_file(sfx_file, blocking=True, load_in_memory=True)
time.sleep(2)
