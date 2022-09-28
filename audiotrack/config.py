import os


class config:
    default_output_track_samplerate: int = 44100
    default_input_track_samplerate: int = 44100

    conversion_path: str = os.path.join(os.getcwd(), "audiotrack_conversions")
    valid_audio_format: str = "wav"
    ffmpeg_executable: str = "ffmpeg"
