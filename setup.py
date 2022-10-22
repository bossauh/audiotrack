from distutils.core import setup
from pathlib import Path

install_requires = [
    "librosa==0.9.2",
    "numpy==1.21.6",
    "sounddevice==0.4.4",
    "soundfile==0.10.3.post1",
    "ffmpy==0.3.0",
]

setup(
    name="audiotrack",
    packages=["audiotrack"],
    version="0.4",
    license="MIT",
    description="A object oriented multi purpose audio library built with python.",
    author="Philippe Mathew",
    author_email="philmattdev@gmail.com",
    url="https://github.com/bossauh/audiotrack",
    download_url="https://github.com/bossauh/audiotrack/archive/refs/tags/v_04.tar.gz",
    keywords=["audio", "recording"],
    install_requires=install_requires,
)
