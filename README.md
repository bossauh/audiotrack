# Audiotrack

---

A object oriented multi purpose audio library built with python. At it's core, audiotrack is just a fancy extension to [sounddevice's](https://python-sounddevice.readthedocs.io/en/0.4.5/) stream classes.

## Installation

---

To install audiotrack, simply run `pip install audiotrack` on your terminal.

## Tracks

---

Think of tracks as layers in a video editing software like premiere. Premiere can have multiple audio tracks playing the same audio at once, and audiotrack can do it as well with the use of the `OutputTrack` class.

But audiotrack goes beyond output, audiotrack also supports the `InputTrack` class which provides a essential method called `.read()`. This method returns data coming from a input device such as a microphone. You can use this data to record your microphone, perform real time speech recognition, or even just pipe it into a `OutputTrack` to monitor your voice in real time.

### Callbacks

---

Each track supports a `callback` parameter which accepts a function. That function can then modify either the incoming input from a microphone before it gets returned to `.read()` or the outgoing audio data before it goes to the output device.

This is useful if you want to let's say remove background noise from a input device before passing it onto somewhere or if you simply just want to add a sound effect to a piece of audio data.

## Demos

---

There are demos included inside the `demos` folder of this repository.

# LICENSE

---

MIT License

Copyright (c) 2022 Philippe Mathew

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
